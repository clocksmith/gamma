#!/usr/bin/env python3
"""Capture the production layer-19 pre-FF hidden state and total adjoint."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import lzma
import os
from pathlib import Path
import shutil
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_top_ff1_input_adjoint_64_q0_v1 as source_parent
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_open_top_ff1_input_adjoint_block128_64_q0_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T123635Z_f1f6615808.json"
)
NORMALIZED_INPUT = ROOT / (
    "results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1/"
    "open-ff1-input.bf16"
)
NORMALIZED_ADJOINT = PARENT_RESULT / "source-exact-ff1-input-adjoint.bf16"
FIXTURE_ROOT = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
FIXTURE_DECISION = FIXTURE_ROOT / "decision.json"
FIXTURE_MANIFEST = FIXTURE_ROOT / "fixture-manifest.json"
FIXTURE_GUARD = FIXTURE_ROOT / "guard.json"
PROBE_SOURCE = ROOT / "tools/nncp_libnc_top_pre_ff_hidden_probe_q0.c"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_v1_materializer.py"
)
RUNNER = Path(__file__).resolve()
SOURCE_CEILING = 2_000_000
STATES = 64
STREAMS = 32
WIDTH = 1024
SAMPLES = STATES * STREAMS
PROBE_PREFIX = "top_pre_ff_"
DECLARATIONS = """static void gamma_top_pre_ff_input_dump(
    NCTensor *value, int layer, int state);
static NCTensor *gamma_top_pre_ff_probe_attach(
    NCTensor *value, int layer, int state);
static int gamma_top_pre_ff_probe_capture(
    void *opaque, NCTensor *gradient, NCTensor *column_index);

"""


def reference(path: Path, identifier: str) -> dict[str, str]:
    return source_parent.source_capture.reference(path, identifier)


def patch_teacher(source: str) -> str:
    capture = source_parent.source_capture
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
        "        gamma_top_pre_ff_probe_set_block(block_idx);\n",
    )
    source = capture.replace_once(
        source,
        "        ff_input = nc_dup_tensor(t0);",
        "        gamma_top_pre_ff_input_dump(t0, layer_idx, output_index);\n"
        "        t0 = gamma_top_pre_ff_probe_attach(\n"
        "            t0, layer_idx, output_index);\n"
        "        ff_input = nc_dup_tensor(t0);",
    )
    source = capture.replace_once(
        source,
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
        "    if (gamma_top_pre_ff_probe_capture(opaque, yg, get_col_index))\n"
        "        return;\n"
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
    )
    return source


def compile_tools(scratch: Path) -> tuple[Path, Path, dict[str, Any]]:
    original = source_parent.patch_teacher
    source_parent.patch_teacher = patch_teacher
    try:
        return source_parent.compile_tools(scratch)
    finally:
        source_parent.patch_teacher = original


def expected_probe_paths() -> set[str]:
    return {
        f"{PROBE_PREFIX}{kind}_s{state:03d}.{extension}"
        for kind in ("input", "adjoint")
        for state in range(STATES)
        for extension in ("bin", "meta")
    }


def fixture_identity(
    manifest: dict[str, Any], parent_manifest: dict[str, Any]
) -> dict[str, Any]:
    expected = expected_probe_paths()
    probe = {
        row["path"]
        for row in manifest["files"]
        if row["path"].startswith(PROBE_PREFIX)
    }
    parent_rows = {
        row["path"]: (row["bytes"], row["sha256"])
        for row in parent_manifest["fixture"]["files"]
    }
    observed_rows = {
        row["path"]: (row["bytes"], row["sha256"])
        for row in manifest["files"]
        if not row["path"].startswith(PROBE_PREFIX)
    }
    mismatches = sorted(
        path
        for path in set(parent_rows) | set(observed_rows)
        if parent_rows.get(path) != observed_rows.get(path)
    )
    return {
        "declaredProbeFileCount": len(probe),
        "declaredProbePopulationExact": probe == expected,
        "missingProbePaths": sorted(expected - probe),
        "unexpectedProbePaths": sorted(probe - expected),
        "nonProbeIdentical": not mismatches,
        "nonProbeMismatches": mismatches,
    }


def combine_probe(directory: Path, kind: str, output: Path) -> None:
    with output.open("wb") as destination:
        for state in range(STATES):
            stem = f"{PROBE_PREFIX}{kind}_s{state:03d}"
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
                or source_parent.source_capture.parse_meta(metadata)
                != expected_meta
            ):
                raise ValueError(f"top pre-FF {kind} state differs: {state}")
            with payload.open("rb") as source:
                shutil.copyfileobj(source, destination, 8 * 1024 * 1024)
    if output.stat().st_size != SAMPLES * WIDTH * 2:
        raise ValueError(f"combined top pre-FF {kind} geometry differs")


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, MATERIALIZER)),
        PROBE_SOURCE.resolve(),
        PROGRAM_DESCRIPTOR.resolve(),
        source_parent.source_capture.FIXTURE_HOOK.resolve(),
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
        raise ValueError("top pre-FF source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-decision", PARENT_DECISION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-guard", PARENT_GUARD),
        ("parent-reflection", PARENT_REFLECTION),
        ("normalized-ff1-input", NORMALIZED_INPUT),
        ("normalized-ff1-input-adjoint", NORMALIZED_ADJOINT),
        ("production-fixture-decision", FIXTURE_DECISION),
        ("production-fixture-manifest", FIXTURE_MANIFEST),
        ("production-fixture-guard", FIXTURE_GUARD),
        ("probe-source", PROBE_SOURCE),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    fixture = json.loads(FIXTURE_DECISION.read_text())
    if not (
        parent["promotionPass"] is True
        and parent["killPass"] is False
        and parent["measurements"]["block128SourceMismatchCount"] == 0
        and parent["measurements"]["unblockedSourceMismatchCount"] > 0
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "supported"
        and reflection["decision"]["verdict"] == "mutate"
        and fixture["promotionPass"] is True
        and fixture["measurements"]["fixtureRepeatByteIdentical"] is True
        and fixture["measurements"]["targetBlockBefore"] == 256
    ):
        raise ValueError("top pre-FF source antecedents are not satisfied")
    for path, expected in source_parent.source_capture.base.EXPECTED.items():
        if not path.is_file() or source_parent.sha256(path) != expected:
            raise ValueError(f"frozen source identity differs: {path}")


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
    if reference(experiment_path, "experiment") != {
        **json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]),
        "id": "experiment",
    }:
        raise ValueError("job and top pre-FF experiment bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("top pre-FF result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("top pre-FF work root was not freshly materialized")

    scratch = WORK / "build"
    scratch.mkdir()
    executable, hook, build = compile_tools(scratch)
    captures = [WORK / "capture-a", WORK / "capture-b"]
    executions = [
        source_parent.source_capture.base.capture(executable, hook, directory)
        for directory in captures
    ]
    manifests = [
        source_parent.source_capture.base.directory_manifest(directory)
        for directory in captures
    ]
    parent_manifest = json.loads(FIXTURE_MANIFEST.read_text())
    identities = [
        fixture_identity(manifest, parent_manifest) for manifest in manifests
    ]
    combined: list[dict[str, Path]] = []
    for label, directory in zip(("a", "b"), captures, strict=True):
        input_path = WORK / f"{label}-pre-ff-hidden.bf16"
        adjoint_path = WORK / f"{label}-pre-ff-hidden-adjoint.bf16"
        combine_probe(directory, "input", input_path)
        combine_probe(directory, "adjoint", adjoint_path)
        combined.append({"input": input_path, "adjoint": adjoint_path})

    input_difference, input_maximum = source_parent.compare_bf16(
        combined[0]["input"], NORMALIZED_INPUT
    )
    adjoint_difference, adjoint_maximum = source_parent.compare_bf16(
        combined[0]["adjoint"], NORMALIZED_ADJOINT
    )
    hidden = RESULT / "source-pre-ff-hidden.bf16"
    adjoint = RESULT / "source-pre-ff-hidden-adjoint.bf16"
    shutil.copyfile(combined[0]["input"], hidden)
    shutil.copyfile(combined[0]["adjoint"], adjoint)
    repeat_identical = (
        manifests[0]["aggregateSha256"] == manifests[1]["aggregateSha256"]
        and combined[0]["input"].read_bytes() == combined[1]["input"].read_bytes()
        and combined[0]["adjoint"].read_bytes()
        == combined[1]["adjoint"].read_bytes()
    )
    probe_exact = all(row["declaredProbePopulationExact"] for row in identities)
    non_probe_mismatches = sum(
        len(row["nonProbeMismatches"]) for row in identities
    )
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
                "normalizedInputDifference": {
                    "mismatchCount": input_difference,
                    "maximumAbsoluteError": input_maximum,
                },
                "normalizedAdjointDifference": {
                    "mismatchCount": adjoint_difference,
                    "maximumAbsoluteError": adjoint_maximum,
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
        "hiddenElementCount": hidden.stat().st_size // 2,
        "adjointElementCount": adjoint.stat().st_size // 2,
        "sourceCaptureDeterministic": repeat_identical,
        "declaredProbeFileCount": sum(
            row["declaredProbeFileCount"] for row in identities
        ),
        "declaredProbePopulationExact": probe_exact,
        "nonProbeFixtureMismatchCount": non_probe_mismatches,
        "fixturePayloadIdentical": non_probe_mismatches == 0,
        "hiddenComparatorLive": hidden.read_bytes() != bytes(hidden.stat().st_size),
        "adjointComparatorLive": adjoint.read_bytes() != bytes(adjoint.stat().st_size),
        "preVsPostNormInputMismatchCount": input_difference,
        "totalVsNormBranchAdjointMismatchCount": adjoint_difference,
        "incrementalSourceBytes": source_closure.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    promotion = source_parent.source_capture.open_parent.evaluate(
        experiment["promotionPredicates"], measurements
    )
    kill = source_parent.source_capture.open_parent.evaluate(
        experiment["killPredicates"], measurements
    )
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": research_contracts.objective_binding(),
        "experiment": reference(experiment_path, "experiment"),
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
            reference(hidden, "source-pre-ff-hidden"),
            reference(adjoint, "source-pre-ff-hidden-adjoint"),
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
