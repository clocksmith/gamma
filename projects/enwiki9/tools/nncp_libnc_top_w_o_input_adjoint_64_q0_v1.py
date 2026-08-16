#!/usr/bin/env python3
"""Capture the production layer-19 w_o input, adjoint, and initial matrix."""

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
import nncp_libnc_top_ff2_input_adjoint_64_q0_v1 as source_capture
import nncp_open_profile_output_bias_gradient_64_q0_retry as fixture_reader
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_w_o_input_adjoint_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_open_top_pre_ff_total_adjoint_64_q0_retry_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T155508Z_53d5388d2c.json"
)
PARENT_ADJOINT = PARENT_RESULT / "source-exact-pre-ff-total-adjoint.bf16"
FIXTURE_ID = "nncp_libnc_profile_update_fixture_64_q3_v1"
FIXTURE_ROOT = ROOT / "results" / FIXTURE_ID
FIXTURE_DECISION = FIXTURE_ROOT / "decision.json"
FIXTURE_MANIFEST = FIXTURE_ROOT / "fixture-manifest.json"
FIXTURE_GUARD = FIXTURE_ROOT / "guard.json"
PARAMETERS = FIXTURE_ROOT / "fixture/parameters_initial.coefs"
RETAINED_GRADIENT = FIXTURE_ROOT / "fixture/gradients/0007_w_o_19.bin"
RETAINED_GRADIENT_META = FIXTURE_ROOT / "fixture/gradients/0007_w_o_19.meta"
PROBE_SOURCE = ROOT / "tools/nncp_libnc_top_w_o_input_probe_q0.c"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_top_w_o_input_adjoint_64_q0_v1_materializer.py"
)
RUNNER = Path(__file__).resolve()
SOURCE_CEILING = 2_000_000
STATES = 64
STREAMS = 32
WIDTH = 1024
SAMPLES = STATES * STREAMS
DECLARATIONS = """static void gamma_top_w_o_input_dump(
    NCTensor *value, int layer, int state);
static NCTensor *gamma_top_w_o_probe_attach(
    NCTensor *value, int layer, int state);
static int gamma_top_w_o_probe_capture(
    void *opaque, NCTensor *gradient, NCTensor *column_index);

"""


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


def patch_teacher(source: str) -> str:
    source = source_capture.capture.base.patch_teacher(source)
    source = source_capture.capture.replace_once(
        source,
        "static FILE *teacher_trace_file;\n",
        PROBE_SOURCE.read_text() + "\nstatic FILE *teacher_trace_file;\n",
    )
    source = source_capture.capture.replace_once(
        source,
        "static NCTensor *layer_norm(",
        DECLARATIONS + "static NCTensor *layer_norm(",
    )
    source = source_capture.capture.replace_once(
        source,
        "    while ((block_idx + n_states) <= block_stride) {\n"
        "        prof_start(PROF_TOTAL);\n",
        "    while ((block_idx + n_states) <= block_stride) {\n"
        "        prof_start(PROF_TOTAL);\n"
        "        gamma_top_w_o_probe_set_block(block_idx);\n",
    )
    source = source_capture.capture.replace_once(
        source,
        "            t0 = concat_head(t0);",
        "            t0 = concat_head(t0);\n"
        "            gamma_top_w_o_input_dump(\n"
        "                t0, layer_idx, output_index);\n"
        "            t0 = gamma_top_w_o_probe_attach(\n"
        "                t0, layer_idx, output_index);",
    )
    source = source_capture.capture.replace_once(
        source,
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
        "    if (gamma_top_w_o_probe_capture(opaque, yg, get_col_index))\n"
        "        return;\n"
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
    )
    return source


def compile_tools(scratch: Path) -> tuple[Path, Path, dict[str, Any]]:
    compiler = os.environ.get("CC", "cc")
    base = source_capture.capture.base
    patched = scratch / "nncp_top_w_o_input_adjoint.c"
    patched.write_text(patch_teacher((base.LIBNC_ROOT / "nncp.c").read_text()))
    nncp_object = scratch / "nncp_top_w_o_input_adjoint.o"
    executable = scratch / "nncp_top_w_o_input_adjoint"
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
            str(source_capture.capture.FIXTURE_HOOK),
            f"-L{base.LIBNC_ROOT}",
            f"-Wl,-rpath,{base.LIBNC_ROOT}",
            "-lnc",
            "-ldl",
            "-o",
            str(hook),
        ],
    ]
    receipts = [source_capture.capture.execute(command, ROOT) for command in commands]
    return executable, hook, {
        "commands": receipts,
        "patchedSourceSha256": sha256(patched),
        "executableSha256": sha256(executable),
        "hookSha256": sha256(hook),
    }


def expected_probe_paths() -> set[str]:
    return {
        f"top_w_o_{kind}_s{state:03d}.{extension}"
        for kind in ("input", "adjoint")
        for state in range(STATES)
        for extension in ("bin", "meta")
    }


def fixture_identity(
    observed: dict[str, Any], parent_manifest: dict[str, Any]
) -> dict[str, Any]:
    expected_probe = expected_probe_paths()
    probe_rows = {
        row["path"] for row in observed["files"] if row["path"].startswith("top_w_o_")
    }
    parent_rows = {
        row["path"]: (row["bytes"], row["sha256"])
        for row in parent_manifest["fixture"]["files"]
    }
    observed_rows = {
        row["path"]: (row["bytes"], row["sha256"])
        for row in observed["files"]
        if not row["path"].startswith("top_w_o_")
    }
    paths = sorted(set(parent_rows) | set(observed_rows))
    mismatches = [
        path for path in paths if parent_rows.get(path) != observed_rows.get(path)
    ]
    return {
        "declaredProbeFileCount": len(probe_rows),
        "declaredProbePopulationExact": probe_rows == expected_probe,
        "missingProbePaths": sorted(expected_probe - probe_rows),
        "unexpectedProbePaths": sorted(probe_rows - expected_probe),
        "nonProbeIdentical": not mismatches,
        "nonProbeMismatches": mismatches,
    }


def combine_probe(directory: Path, kind: str, output: Path) -> None:
    with output.open("wb") as destination:
        for state in range(STATES):
            stem = f"top_w_o_{kind}_s{state:03d}"
            payload = directory / f"{stem}.bin"
            metadata = directory / f"{stem}.meta"
            expected_meta = {
                "kind": kind,
                "state": str(state),
                "item_type": "1",
                "item_size": "2",
                "dims": f"{WIDTH},{STREAMS}",
                "byte_order": "little",
            }
            if (
                not payload.is_file()
                or payload.stat().st_size != WIDTH * STREAMS * 2
                or not metadata.is_file()
                or source_capture.capture.parse_meta(metadata) != expected_meta
            ):
                raise ValueError(f"source top w_o input {kind} state differs: {state}")
            with payload.open("rb") as source:
                shutil.copyfileobj(source, destination, 8 * 1024 * 1024)
    if output.stat().st_size != SAMPLES * WIDTH * 2:
        raise ValueError(f"combined top w_o input {kind} geometry differs")


def extract_initial_matrix(output: Path) -> dict[str, Any]:
    container = fixture_reader.Container(PARAMETERS)
    try:
        record = container.record("w_o_19")
        type_name = fixture_reader.TYPE_CONTRACT[record["type"]][0]
        if (
            type_name != "BF16"
            or record["dimensions"] != [WIDTH, WIDTH]
            or record["bytes"] != WIDTH * WIDTH * 2
        ):
            raise ValueError("initial w_o_19 parameter geometry differs")
        output.write_bytes(container.payload("w_o_19"))
        return {
            "name": "w_o_19",
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
        source_capture.capture.FIXTURE_HOOK.resolve(),
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
        raise ValueError("top w_o input source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-decision", PARENT_DECISION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-guard", PARENT_GUARD),
        ("parent-reflection", PARENT_REFLECTION),
        ("parent-pre-w-o-output-adjoint", PARENT_ADJOINT),
        ("production-fixture-decision", FIXTURE_DECISION),
        ("production-fixture-manifest", FIXTURE_MANIFEST),
        ("production-fixture-guard", FIXTURE_GUARD),
        ("production-initial-parameters", PARAMETERS),
        ("retained-w-o-gradient", RETAINED_GRADIENT),
        ("retained-w-o-gradient-meta", RETAINED_GRADIENT_META),
        ("probe-source", PROBE_SOURCE),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    fixture = json.loads(FIXTURE_DECISION.read_text())
    retained_meta = source_capture.capture.parse_meta(RETAINED_GRADIENT_META)
    if not (
        parent["promotionPass"] is True
        and parent["killPass"] is False
        and parent["measurements"]["totalAdjointMismatchCount"] == 0
        and parent["measurements"]["evaluationReplayIdentical"] is True
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "supported"
        and reflection["decision"]["verdict"] == "mutate"
        and fixture["promotionPass"] is True
        and fixture["measurements"]["fixtureRepeatByteIdentical"] is True
        and fixture["measurements"]["targetBlockBefore"] == 256
        and retained_meta
        == {
            "index": "7",
            "name": "w_o_19",
            "item_type": "1",
            "item_size": "2",
            "dims": "1024,1024",
            "byte_order": "little",
            "column_index": "none",
        }
    ):
        raise ValueError("source top w_o input antecedents are not satisfied")
    for path, expected in source_capture.capture.base.EXPECTED.items():
        if not path.is_file() or sha256(path) != expected:
            raise ValueError(f"frozen source input identity differs: {path}")


def build_result(
    experiment_path: Path,
    experiment: dict[str, Any],
    revision: dict[str, Any],
    measurements: dict[str, bool | int | float],
    artifacts: list[dict[str, str]],
) -> dict[str, Any]:
    promotion = source_capture.capture.open_parent.evaluate(
        experiment["promotionPredicates"], measurements
    )
    kill = source_capture.capture.open_parent.evaluate(
        experiment["killPredicates"], measurements
    )
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    return {
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
        "artifacts": artifacts,
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }


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
        raise ValueError("job and source top w_o experiment bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("source top w_o result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("source top w_o work root was not freshly materialized")

    scratch = WORK / "build"
    scratch.mkdir()
    executable, hook, build = compile_tools(scratch)
    captures = [WORK / "capture-a", WORK / "capture-b"]
    executions = [
        source_capture.capture.base.capture(executable, hook, directory)
        for directory in captures
    ]
    manifests = [
        source_capture.capture.base.directory_manifest(directory)
        for directory in captures
    ]
    parent_manifest = json.loads(FIXTURE_MANIFEST.read_text())
    identities = [fixture_identity(manifest, parent_manifest) for manifest in manifests]
    combined: list[dict[str, Path]] = []
    for label, directory in zip(("a", "b"), captures, strict=True):
        input_path = WORK / f"{label}-source-w-o-input.bf16"
        adjoint_path = WORK / f"{label}-source-w-o-input-adjoint.bf16"
        combine_probe(directory, "input", input_path)
        combine_probe(directory, "adjoint", adjoint_path)
        combined.append({"input": input_path, "adjoint": adjoint_path})

    matrix_work = WORK / "initial-w-o-19.bf16"
    matrix_receipt = extract_initial_matrix(matrix_work)
    source_input = RESULT / "source-w-o-input.bf16"
    source_adjoint = RESULT / "source-w-o-input-adjoint.bf16"
    initial_matrix = RESULT / "source-initial-w-o-19.bf16"
    shutil.copyfile(combined[0]["input"], source_input)
    shutil.copyfile(combined[0]["adjoint"], source_adjoint)
    shutil.copyfile(matrix_work, initial_matrix)
    repeat_identical = (
        manifests[0]["aggregateSha256"] == manifests[1]["aggregateSha256"]
        and combined[0]["input"].read_bytes() == combined[1]["input"].read_bytes()
        and combined[0]["adjoint"].read_bytes()
        == combined[1]["adjoint"].read_bytes()
    )
    probe_exact = all(row["declaredProbePopulationExact"] for row in identities)
    non_probe_identical = all(row["nonProbeIdentical"] for row in identities)
    non_probe_mismatch_count = sum(
        len(row["nonProbeMismatches"]) for row in identities
    )
    probe_file_count = sum(row["declaredProbeFileCount"] for row in identities)
    source_closure = RESULT / "incremental_source.tar.xz"
    source_package(source_closure)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "build": build,
                "captureManifests": manifests,
                "executions": executions,
                "fixtureIdentity": identities,
                "initialMatrix": matrix_receipt,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "captureCount": len(captures),
        "sampleCount": SAMPLES,
        "sourceInputElementCount": source_input.stat().st_size // 2,
        "sourceAdjointElementCount": source_adjoint.stat().st_size // 2,
        "initialMatrixElementCount": initial_matrix.stat().st_size // 2,
        "sourceCaptureDeterministic": repeat_identical,
        "declaredProbeFileCount": probe_file_count,
        "declaredProbePopulationExact": probe_exact,
        "fixturePayloadIdentical": non_probe_identical,
        "fixturePayloadMismatchCount": non_probe_mismatch_count,
        "inputLive": any(source_input.read_bytes()),
        "adjointLive": any(source_adjoint.read_bytes()),
        "incrementalSourceBytes": source_closure.stat().st_size,
        "guardedWorkRootPass": False,
    }
    artifacts = [
        reference(execution_path, "execution"),
        reference(source_input, "source-w-o-input"),
        reference(source_adjoint, "source-w-o-input-adjoint"),
        reference(initial_matrix, "source-initial-w-o-19"),
        reference(source_closure, "incremental-source-package"),
    ]
    precleanup = RESULT / "decision.precleanup.json"
    precleanup.write_text(
        json.dumps(
            build_result(
                experiment_path, experiment, revision, measurements, artifacts
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    research_contracts.validate_artifact(precleanup)
    shutil.rmtree(WORK)
    measurements["guardedWorkRootPass"] = not WORK.exists()
    result = build_result(
        experiment_path, experiment, revision, measurements, artifacts
    )
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(output)
    precleanup.unlink()
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
