#!/usr/bin/env python3
"""Capture the production top-FF1 input adjoint and initial matrix."""

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
import nncp_libnc_top_ff2_input_adjoint_64_q0_v1 as parent
import nncp_open_profile_output_bias_gradient_64_q0_retry as fixture_reader
import research_contracts


source_capture = parent.capture
ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_ff1_input_adjoint_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
OPEN_ID = "nncp_open_profile_top_ff1_gradient_post_add_64_q0_v1"
OPEN_RESULT = ROOT / "results" / OPEN_ID
OPEN_DECISION = OPEN_RESULT / "decision.json"
OPEN_EXECUTION = OPEN_RESULT / "execution.json"
OPEN_GUARD = OPEN_RESULT / "guard.json"
OPEN_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T121133Z_b2c70f9ec5.json"
)
OPEN_INPUT = ROOT / (
    "results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1/"
    "open-ff1-input.bf16"
)
OPEN_OUTPUT_ADJOINT = ROOT / (
    "results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/"
    "open-ff1-output-residual.bf16"
)
FIXTURE_ID = "nncp_libnc_profile_update_fixture_64_q3_v1"
FIXTURE_ROOT = ROOT / "results" / FIXTURE_ID
FIXTURE_DECISION = FIXTURE_ROOT / "decision.json"
FIXTURE_MANIFEST = FIXTURE_ROOT / "fixture-manifest.json"
FIXTURE_GUARD = FIXTURE_ROOT / "guard.json"
PARAMETERS = FIXTURE_ROOT / "fixture/parameters_initial.coefs"
PROBE_SOURCE = ROOT / "tools/nncp_libnc_top_ff1_input_probe_q0.c"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_top_ff1_input_adjoint_64_q0_v1_materializer.py"
)
RUNNER = Path(__file__).resolve()
SOURCE_CEILING = 2_000_000
STATES = 64
STREAMS = 32
INNER = 1024
SAMPLES = STATES * STREAMS
MATRIX_OUTPUTS = 6144
DECLARATIONS = """static void gamma_top_ff1_input_dump(
    NCTensor *value, int layer, int state);
static NCTensor *gamma_top_ff1_probe_attach(
    NCTensor *value, int layer, int state);
static int gamma_top_ff1_probe_capture(
    void *opaque, NCTensor *gradient, NCTensor *column_index);

"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def patch_teacher(source: str) -> str:
    source = source_capture.base.patch_teacher(source)
    source = source_capture.replace_once(
        source,
        "static FILE *teacher_trace_file;\n",
        PROBE_SOURCE.read_text() + "\nstatic FILE *teacher_trace_file;\n",
    )
    source = source_capture.replace_once(
        source,
        "static NCTensor *layer_norm(",
        DECLARATIONS + "static NCTensor *layer_norm(",
    )
    source = source_capture.replace_once(
        source,
        "    while ((block_idx + n_states) <= block_stride) {\n"
        "        prof_start(PROF_TOTAL);\n",
        "    while ((block_idx + n_states) <= block_stride) {\n"
        "        prof_start(PROF_TOTAL);\n"
        "        gamma_top_ff1_probe_set_block(block_idx);\n",
    )
    source = source_capture.replace_once(
        source,
        "        t0 = nc_matmul(nc_dup_tensor(tl->ff1), t0);",
        "        gamma_top_ff1_input_dump(t0, layer_idx, output_index);\n"
        "        t0 = gamma_top_ff1_probe_attach(\n"
        "            t0, layer_idx, output_index);\n"
        "        t0 = nc_matmul(nc_dup_tensor(tl->ff1), t0);",
    )
    source = source_capture.replace_once(
        source,
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
        "    if (gamma_top_ff1_probe_capture(opaque, yg, get_col_index))\n"
        "        return;\n"
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
    )
    return source


def compile_tools(scratch: Path) -> tuple[Path, Path, dict[str, Any]]:
    compiler = os.environ.get("CC", "cc")
    patched = scratch / "nncp_top_ff1_input_adjoint.c"
    patched.write_text(
        patch_teacher((source_capture.base.LIBNC_ROOT / "nncp.c").read_text())
    )
    nncp_object = scratch / "nncp_top_ff1_input_adjoint.o"
    executable = scratch / "nncp_top_ff1_input_adjoint"
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
            f"-I{source_capture.base.LIBNC_ROOT}",
            "-c",
            str(patched),
            "-o",
            str(nncp_object),
        ],
        [
            compiler,
            f"-Wl,-rpath,{source_capture.base.LIBNC_ROOT}",
            "-o",
            str(executable),
            str(nncp_object),
            *[
                str(source_capture.base.LIBNC_ROOT / name)
                for name in (
                    "cmdopt.o",
                    "cp_utils.o",
                    "arith.o",
                    "preprocess.o",
                    "cutils.o",
                )
            ],
            str(source_capture.base.LIBNC_ROOT / "libnc.so"),
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
            f"-I{source_capture.base.LIBNC_ROOT}",
            str(source_capture.FIXTURE_HOOK),
            f"-L{source_capture.base.LIBNC_ROOT}",
            f"-Wl,-rpath,{source_capture.base.LIBNC_ROOT}",
            "-lnc",
            "-ldl",
            "-o",
            str(hook),
        ],
    ]
    receipts = [source_capture.execute(command, ROOT) for command in commands]
    return executable, hook, {
        "commands": receipts,
        "patchedSourceSha256": sha256(patched),
        "executableSha256": sha256(executable),
        "hookSha256": sha256(hook),
    }


def combine_probe(directory: Path, kind: str, output: Path) -> None:
    with output.open("wb") as destination:
        for state in range(STATES):
            stem = f"top_ff1_{kind}_s{state:03d}"
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
                or source_capture.parse_meta(metadata) != expected_meta
            ):
                raise ValueError(f"source FF1-input {kind} state differs: {state}")
            with payload.open("rb") as source:
                shutil.copyfileobj(source, destination, 8 * 1024 * 1024)
    if output.stat().st_size != SAMPLES * INNER * 2:
        raise ValueError(f"combined FF1-input {kind} geometry differs")


def extract_initial_matrix(output: Path) -> dict[str, Any]:
    container = fixture_reader.Container(PARAMETERS)
    try:
        record = container.record("ff1_19")
        type_name = fixture_reader.TYPE_CONTRACT[record["type"]][0]
        if (
            type_name != "BF16"
            or record["dimensions"] != [MATRIX_OUTPUTS, INNER]
            or record["bytes"] != MATRIX_OUTPUTS * INNER * 2
        ):
            raise ValueError("initial ff1_19 parameter geometry differs")
        output.write_bytes(container.payload("ff1_19"))
        return {
            "name": "ff1_19",
            "type": type_name,
            "dimensions": record["dimensions"],
            "bytes": record["bytes"],
            "sha256": sha256(output),
        }
    finally:
        container.close()


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, MATERIALIZER)),
        PROBE_SOURCE.resolve(),
        PROGRAM_DESCRIPTOR.resolve(),
        source_capture.FIXTURE_HOOK.resolve(),
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
        raise ValueError("FF1-input source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("open-decision", OPEN_DECISION),
        ("open-execution", OPEN_EXECUTION),
        ("open-guard", OPEN_GUARD),
        ("open-reflection", OPEN_REFLECTION),
        ("open-ff1-input", OPEN_INPUT),
        ("open-ff1-output-adjoint", OPEN_OUTPUT_ADJOINT),
        ("production-fixture-decision", FIXTURE_DECISION),
        ("production-fixture-manifest", FIXTURE_MANIFEST),
        ("production-fixture-guard", FIXTURE_GUARD),
        ("production-initial-parameters", PARAMETERS),
        ("probe-source", PROBE_SOURCE),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != source_capture.reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    opened = json.loads(OPEN_DECISION.read_text())
    reflection = json.loads(OPEN_REFLECTION.read_text())
    fixture = json.loads(FIXTURE_DECISION.read_text())
    if not (
        opened["promotionPass"] is True
        and opened["killPass"] is False
        and opened["measurements"]["treatmentMismatchCount"] == 0
        and opened["measurements"]["gradientElementCount"] == 6291456
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "supported"
        and reflection["decision"]["verdict"] == "mutate"
        and fixture["promotionPass"] is True
        and fixture["measurements"]["fixtureRepeatByteIdentical"] is True
        and fixture["measurements"]["targetBlockBefore"] == 256
    ):
        raise ValueError("source FF1-input adjoint antecedents are not satisfied")
    for path, expected in source_capture.base.EXPECTED.items():
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
    if source_capture.reference(experiment_path) != json.loads(
        os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]
    ):
        raise ValueError("job and source FF1-input experiment bindings differ")
    candidate_revision = json.loads(
        os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"]
    )
    if candidate_revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("source FF1-input result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("source FF1-input work root was not freshly materialized")

    scratch = WORK / "build"
    scratch.mkdir()
    executable, hook, build = compile_tools(scratch)
    captures = [WORK / "capture-a", WORK / "capture-b"]
    executions = [
        source_capture.base.capture(executable, hook, directory)
        for directory in captures
    ]
    manifests = [
        source_capture.base.directory_manifest(directory) for directory in captures
    ]
    parent_manifest = json.loads(FIXTURE_MANIFEST.read_text())
    identities = [
        source_capture.fixture_identity(manifest, parent_manifest)
        for manifest in manifests
    ]
    combined: list[dict[str, Path]] = []
    for label, directory in zip(("a", "b"), captures, strict=True):
        input_path = WORK / f"{label}-source-ff1-input.bf16"
        adjoint_path = WORK / f"{label}-source-ff1-input-adjoint.bf16"
        combine_probe(directory, "input", input_path)
        combine_probe(directory, "adjoint", adjoint_path)
        combined.append({"input": input_path, "adjoint": adjoint_path})

    input_mismatches, input_maximum = parent.compare_bf16(
        combined[0]["input"], OPEN_INPUT
    )
    matrix_work = WORK / "initial-ff1-19.bf16"
    matrix_receipt = extract_initial_matrix(matrix_work)
    source_input = RESULT / "source-ff1-input.bf16"
    source_adjoint = RESULT / "source-ff1-input-adjoint.bf16"
    initial_matrix = RESULT / "source-initial-ff1-19.bf16"
    shutil.copyfile(combined[0]["input"], source_input)
    shutil.copyfile(combined[0]["adjoint"], source_adjoint)
    shutil.copyfile(matrix_work, initial_matrix)
    repeat_identical = (
        manifests[0]["aggregateSha256"] == manifests[1]["aggregateSha256"]
        and combined[0]["input"].read_bytes() == combined[1]["input"].read_bytes()
        and combined[0]["adjoint"].read_bytes()
        == combined[1]["adjoint"].read_bytes()
    )
    comparator_live = source_adjoint.read_bytes() != bytes(
        source_adjoint.stat().st_size
    )
    fixture_identical = all(identity[0] for identity in identities)
    fixture_mismatch_count = sum(len(identity[1]) for identity in identities)
    source_closure = RESULT / "incremental_source.tar.xz"
    source_package(source_closure)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "build": build,
                "captureManifests": manifests,
                "executions": executions,
                "fixtureIdentity": [
                    {"identical": value[0], "mismatches": value[1]}
                    for value in identities
                ],
                "initialMatrix": matrix_receipt,
                "sourceInputComparison": {
                    "mismatchCount": input_mismatches,
                    "maximumAbsoluteError": input_maximum,
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
        "captureCount": len(captures),
        "sampleCount": SAMPLES,
        "sourceInputElementCount": source_input.stat().st_size // 2,
        "sourceAdjointElementCount": source_adjoint.stat().st_size // 2,
        "initialMatrixElementCount": initial_matrix.stat().st_size // 2,
        "sourceInputMismatchCount": input_mismatches,
        "maximumSourceInputAbsoluteError": input_maximum,
        "sourceCaptureDeterministic": repeat_identical,
        "fixturePayloadIdentical": fixture_identical,
        "fixturePayloadMismatchCount": fixture_mismatch_count,
        "comparatorLive": comparator_live,
        "incrementalSourceBytes": source_closure.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    promotion = source_capture.open_parent.evaluate(
        experiment["promotionPredicates"], measurements
    )
    kill = source_capture.open_parent.evaluate(
        experiment["killPredicates"], measurements
    )
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": research_contracts.objective_binding(),
        "experiment": source_capture.reference(experiment_path),
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
            source_capture.reference(execution_path, "execution"),
            source_capture.reference(source_input, "source-ff1-input"),
            source_capture.reference(source_adjoint, "source-ff1-input-adjoint"),
            source_capture.reference(initial_matrix, "source-initial-ff1-19"),
            source_capture.reference(source_closure, "incremental-source-package"),
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
