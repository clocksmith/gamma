#!/usr/bin/env python3
"""Capture the production FF2-input adjoint and compare the open transpose."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_top_ff2_adjoint_64_q0 as capture
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_ff2_input_adjoint_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
OPEN_ID = "nncp_open_profile_top_ff1_bias_gradient_64_q0_v1"
OPEN_RESULT = ROOT / "results" / OPEN_ID
OPEN_DECISION = OPEN_RESULT / "decision.json"
OPEN_EXECUTION = OPEN_RESULT / "execution.json"
OPEN_GUARD = OPEN_RESULT / "guard.json"
OPEN_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T084751Z_2949ede196.json"
)
OPEN_RESIDUAL = OPEN_RESULT / "open-ff2-input-residual.bf16"
FIXTURE_ID = "nncp_libnc_profile_update_fixture_64_q3_v1"
FIXTURE_ROOT = ROOT / "results" / FIXTURE_ID
FIXTURE_DECISION = FIXTURE_ROOT / "decision.json"
FIXTURE_MANIFEST = FIXTURE_ROOT / "fixture-manifest.json"
FIXTURE_GUARD = FIXTURE_ROOT / "guard.json"
PROBE_SOURCE = ROOT / "tools/nncp_libnc_top_ff2_input_probe_q0.c"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_top_ff2_input_adjoint_64_q0_v1_materializer.py"
)
RUNNER = Path(__file__).resolve()
SOURCE_CEILING = 2_000_000
STATES = 64
STREAMS = 32
INNER = 3072
DECLARATIONS = """static void gamma_top_ff2_input_dump(
    NCTensor *value, int layer, int state);
static NCTensor *gamma_top_ff2_probe_attach(
    NCTensor *value, int layer, int state);
static int gamma_top_ff2_probe_capture(
    void *opaque, NCTensor *gradient, NCTensor *column_index);

"""


def patch_teacher(source: str) -> str:
    source = capture.base.patch_teacher(source)
    source = capture.replace_once(
        source,
        "static FILE *teacher_trace_file;\n",
        PROBE_SOURCE.read_text() + "\nstatic FILE *teacher_trace_file;\n",
    )
    source = capture.replace_once(
        source,
        "static NCTensor *layer_norm(",
        DECLARATIONS + "static NCTensor *layer_norm(",
    )
    source = capture.replace_once(
        source,
        "    while ((block_idx + n_states) <= block_stride) {\n"
        "        prof_start(PROF_TOTAL);\n",
        "    while ((block_idx + n_states) <= block_stride) {\n"
        "        prof_start(PROF_TOTAL);\n"
        "        gamma_top_ff2_probe_set_block(block_idx);\n",
    )
    source = capture.replace_once(
        source,
        "        t0 = nc_matmul(nc_dup_tensor(tl->ff2), t0);",
        "        gamma_top_ff2_input_dump(t0, layer_idx, output_index);\n"
        "        t0 = gamma_top_ff2_probe_attach(\n"
        "            t0, layer_idx, output_index);\n"
        "        t0 = nc_matmul(nc_dup_tensor(tl->ff2), t0);",
    )
    source = capture.replace_once(
        source,
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
        "    if (gamma_top_ff2_probe_capture(opaque, yg, get_col_index))\n"
        "        return;\n"
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
    )
    return source


def compile_tools(scratch: Path) -> tuple[Path, Path, dict[str, Any]]:
    compiler = os.environ.get("CC", "cc")
    patched = scratch / "nncp_top_ff2_input_adjoint.c"
    patched.write_text(patch_teacher((capture.base.LIBNC_ROOT / "nncp.c").read_text()))
    nncp_object = scratch / "nncp_top_ff2_input_adjoint.o"
    executable = scratch / "nncp_top_ff2_input_adjoint"
    hook = scratch / "nncp_profile_update_fixture_hook_q3.so"
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
            f"-I{capture.base.LIBNC_ROOT}",
            "-c",
            str(patched),
            "-o",
            str(nncp_object),
        ],
        [
            compiler,
            f"-Wl,-rpath,{capture.base.LIBNC_ROOT}",
            "-o",
            str(executable),
            str(nncp_object),
            *[
                str(capture.base.LIBNC_ROOT / name)
                for name in (
                    "cmdopt.o",
                    "cp_utils.o",
                    "arith.o",
                    "preprocess.o",
                    "cutils.o",
                )
            ],
            str(capture.base.LIBNC_ROOT / "libnc.so"),
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
            f"-I{capture.base.LIBNC_ROOT}",
            str(capture.FIXTURE_HOOK),
            f"-L{capture.base.LIBNC_ROOT}",
            f"-Wl,-rpath,{capture.base.LIBNC_ROOT}",
            "-lnc",
            "-ldl",
            "-o",
            str(hook),
        ],
    ]
    receipts = [capture.execute(command, ROOT) for command in commands]
    return executable, hook, {
        "commands": receipts,
        "patchedSourceSha256": capture.sha256(patched),
        "executableSha256": capture.sha256(executable),
        "hookSha256": capture.sha256(hook),
    }


def combine_probe(directory: Path, kind: str, output: Path) -> None:
    with output.open("wb") as destination:
        for state in range(STATES):
            stem = f"top_ff2_{kind}_s{state:03d}"
            payload = directory / f"{stem}.bin"
            metadata = directory / f"{stem}.meta"
            expected_meta = {
                "kind": kind,
                "state": str(state),
                "item_type": "1",
                "item_size": "2",
                "dims": f"{INNER},{STREAMS}",
                "byte_order": "little",
            }
            if (
                not payload.is_file()
                or payload.stat().st_size != INNER * STREAMS * 2
                or not metadata.is_file()
                or capture.parse_meta(metadata) != expected_meta
            ):
                raise ValueError(f"source FF2-input {kind} state differs: {state}")
            with payload.open("rb") as source:
                shutil.copyfileobj(source, destination, 8 * 1024 * 1024)
    if output.stat().st_size != STATES * STREAMS * INNER * 2:
        raise ValueError(f"combined FF2-input {kind} geometry differs")


def compare_bf16(left: Path, right: Path) -> tuple[int, float]:
    left_bytes = left.read_bytes()
    right_bytes = right.read_bytes()
    if len(left_bytes) != len(right_bytes) or len(left_bytes) % 2:
        raise ValueError("FF2-input comparison geometry differs")
    mismatches = 0
    maximum = 0.0
    for index in range(0, len(left_bytes), 2):
        left_word = int.from_bytes(left_bytes[index : index + 2], "little")
        right_word = int.from_bytes(right_bytes[index : index + 2], "little")
        if left_word != right_word:
            mismatches += 1
            left_value = capture.open_parent.parent.bf16_to_float(left_word)
            right_value = capture.open_parent.parent.bf16_to_float(right_word)
            maximum = max(maximum, abs(left_value - right_value))
    return mismatches, maximum


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, MATERIALIZER)),
        PROBE_SOURCE.resolve(),
        PROGRAM_DESCRIPTOR.resolve(),
        capture.FIXTURE_HOOK.resolve(),
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
        raise ValueError("FF2-input source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("open-decision", OPEN_DECISION),
        ("open-execution", OPEN_EXECUTION),
        ("open-guard", OPEN_GUARD),
        ("open-reflection", OPEN_REFLECTION),
        ("open-ff2-input-residual", OPEN_RESIDUAL),
        ("production-fixture-decision", FIXTURE_DECISION),
        ("production-fixture-manifest", FIXTURE_MANIFEST),
        ("production-fixture-guard", FIXTURE_GUARD),
        ("probe-source", PROBE_SOURCE),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != capture.reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    opened = json.loads(OPEN_DECISION.read_text())
    reflection = json.loads(OPEN_REFLECTION.read_text())
    fixture = json.loads(FIXTURE_DECISION.read_text())
    if not (
        opened["promotionPass"] is False
        and opened["killPass"] is True
        and opened["measurements"]["topFf1BiasMismatchCount"] == 4708
        and opened["measurements"]["openBackwardDeterministic"] is True
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "refuted"
        and reflection["decision"]["verdict"] == "mutate"
        and fixture["promotionPass"] is True
        and fixture["measurements"]["fixtureRepeatByteIdentical"] is True
        and fixture["measurements"]["targetBlockBefore"] == 256
    ):
        raise ValueError("source FF2-input adjoint antecedents are not satisfied")
    for path, expected in capture.base.EXPECTED.items():
        if not path.is_file() or capture.sha256(path) != expected:
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
    if capture.reference(experiment_path) != json.loads(
        os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]
    ):
        raise ValueError("job and source experiment bindings differ")
    candidate_revision = json.loads(
        os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"]
    )
    if candidate_revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("source FF2-input result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("source FF2-input work root was not freshly materialized")

    scratch = WORK / "build"
    scratch.mkdir()
    executable, hook, build = compile_tools(scratch)
    captures = [WORK / "capture-a", WORK / "capture-b"]
    executions = [
        capture.base.capture(executable, hook, directory)
        for directory in captures
    ]
    manifests = [capture.base.directory_manifest(directory) for directory in captures]
    parent_manifest = json.loads(FIXTURE_MANIFEST.read_text())
    identities = [
        capture.fixture_identity(manifest, parent_manifest) for manifest in manifests
    ]
    combined: list[dict[str, Path]] = []
    for label, directory in zip(("a", "b"), captures, strict=True):
        input_path = WORK / f"{label}-source-ff2-input.bf16"
        adjoint_path = WORK / f"{label}-source-ff2-input-adjoint.bf16"
        combine_probe(directory, "input", input_path)
        combine_probe(directory, "adjoint", adjoint_path)
        combined.append({"input": input_path, "adjoint": adjoint_path})

    mismatch_count, maximum_error = compare_bf16(
        combined[0]["adjoint"], OPEN_RESIDUAL
    )
    source_input = RESULT / "source-ff2-input.bf16"
    source_adjoint = RESULT / "source-ff2-input-adjoint.bf16"
    shutil.copyfile(combined[0]["input"], source_input)
    shutil.copyfile(combined[0]["adjoint"], source_adjoint)
    repeat_identical = (
        manifests[0]["aggregateSha256"] == manifests[1]["aggregateSha256"]
        and combined[0]["input"].read_bytes() == combined[1]["input"].read_bytes()
        and combined[0]["adjoint"].read_bytes()
        == combined[1]["adjoint"].read_bytes()
    )
    comparator_live = source_adjoint.read_bytes() != bytes(source_adjoint.stat().st_size)
    fixture_identical = all(identity[0] for identity in identities)
    fixture_mismatch_count = sum(len(identity[1]) for identity in identities)
    source_closure = RESULT / "incremental_source.tar.xz"
    source_package(source_closure)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "build": build,
                "executions": executions,
                "captureManifests": manifests,
                "fixtureIdentity": [
                    {"identical": value[0], "mismatches": value[1]}
                    for value in identities
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
        "captureCount": len(captures),
        "sampleCount": STATES * STREAMS,
        "sourceInputElementCount": source_input.stat().st_size // 2,
        "sourceAdjointElementCount": source_adjoint.stat().st_size // 2,
        "sourceCaptureDeterministic": repeat_identical,
        "fixturePayloadIdentical": fixture_identical,
        "fixturePayloadMismatchCount": fixture_mismatch_count,
        "openResidualMismatchCount": mismatch_count,
        "maximumOpenResidualAbsoluteError": maximum_error,
        "comparatorLive": comparator_live,
        "incrementalSourceBytes": source_closure.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    promotion = capture.open_parent.evaluate(
        experiment["promotionPredicates"], measurements
    )
    kill = capture.open_parent.evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": research_contracts.objective_binding(),
        "experiment": capture.reference(experiment_path),
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
            capture.reference(execution_path, "execution"),
            capture.reference(source_input, "source-ff2-input"),
            capture.reference(source_adjoint, "source-ff2-input-adjoint"),
            capture.reference(source_closure, "incremental-source-package"),
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
