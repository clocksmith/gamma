#!/usr/bin/env python3
"""Capture the source layer-19 pre-FF normalization-only input adjoint."""

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
import nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_v1 as source_base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_open_top_pre_ff_residual_conversion_order_64_q0_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T135007Z_c0fde22dd2.json"
)
OPEN_RESULT = ROOT / (
    "results/nncp_open_top_pre_ff_rmsnorm_backward_state_reduce_64_q0_v1"
)
OPEN_BRANCH = OPEN_RESULT / "open-pre-ff-norm-input-adjoint.bf16"
SOURCE_RESULT = ROOT / "results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2"
SOURCE_HIDDEN = SOURCE_RESULT / "source-pre-ff-hidden.bf16"
SOURCE_TOTAL = SOURCE_RESULT / "source-pre-ff-hidden-adjoint.bf16"
FIXTURE_ROOT = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
FIXTURE_DECISION = FIXTURE_ROOT / "decision.json"
FIXTURE_MANIFEST = FIXTURE_ROOT / "fixture-manifest.json"
FIXTURE_GUARD = FIXTURE_ROOT / "guard.json"
PROBE_SOURCE = ROOT / "tools/nncp_libnc_top_pre_ff_norm_branch_probe_q0.c"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
RUNNER = Path(__file__).resolve()
FREEZER = ROOT / (
    "tools/nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_materializer.py"
)
SOURCE_CEILING = 2_000_000
STATES = 64
STREAMS = 32
WIDTH = 1024
SAMPLES = STATES * STREAMS
PROBE_PREFIX = "pre_ff_norm_"
DECLARATIONS = """static void gamma_pre_ff_norm_input_dump(
    NCTensor *value, int layer, int state);
static NCTensor *gamma_pre_ff_norm_probe_attach(
    NCTensor *value, int layer, int state);
static int gamma_pre_ff_norm_probe_capture(
    void *opaque, NCTensor *gradient, NCTensor *column_index);

"""


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    return source_base.reference(path, identifier or path.stem)


def patch_teacher(source: str) -> str:
    capture = source_base.source_parent.source_capture
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
        "        gamma_pre_ff_norm_probe_set_block(block_idx);\n",
    )
    source = capture.replace_once(
        source,
        "        ff_input = nc_dup_tensor(t0);\n"
        "        if (s->ln_flags & LN_PRE) {\n"
        "            t0 = layer_norm(t0, tl->ln_g2, tl->ln_b2, s->ln_flags);\n"
        "        }",
        "        ff_input = nc_dup_tensor(t0);\n"
        "        if (s->ln_flags & LN_PRE) {\n"
        "            gamma_pre_ff_norm_input_dump(\n"
        "                t0, layer_idx, output_index);\n"
        "            t0 = gamma_pre_ff_norm_probe_attach(\n"
        "                t0, layer_idx, output_index);\n"
        "            t0 = layer_norm(t0, tl->ln_g2, tl->ln_b2, s->ln_flags);\n"
        "        }",
    )
    source = capture.replace_once(
        source,
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
        "    if (gamma_pre_ff_norm_probe_capture(opaque, yg, get_col_index))\n"
        "        return;\n"
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
    )
    return source


def compile_tools(scratch: Path) -> tuple[Path, Path, dict[str, Any]]:
    parent = source_base.source_parent
    original = parent.patch_teacher
    parent.patch_teacher = patch_teacher
    try:
        return parent.compile_tools(scratch)
    finally:
        parent.patch_teacher = original


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
        row["path"] for row in manifest["files"]
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
        path for path in set(parent_rows) | set(observed_rows)
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
    parse_meta = source_base.source_parent.source_capture.parse_meta
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
                or parse_meta(metadata) != expected_meta
            ):
                raise ValueError(
                    f"pre-FF normalization {kind} state differs: {state}"
                )
            with payload.open("rb") as source:
                shutil.copyfileobj(source, destination, 8 * 1024 * 1024)
    if output.stat().st_size != SAMPLES * WIDTH * 2:
        raise ValueError(f"combined pre-FF normalization {kind} geometry differs")


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, FREEZER)),
        PROBE_SOURCE.resolve(),
        PROGRAM_DESCRIPTOR.resolve(),
        source_base.source_parent.source_capture.FIXTURE_HOOK.resolve(),
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
        raise ValueError("pre-FF normalization source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-decision", PARENT_RESULT / "decision.json"),
        ("parent-execution", PARENT_RESULT / "execution.json"),
        ("parent-guard", PARENT_RESULT / "guard.json"),
        ("parent-reflection", PARENT_REFLECTION),
        ("open-normalization-branch-adjoint", OPEN_BRANCH),
        ("source-pre-ff-hidden", SOURCE_HIDDEN),
        ("source-pre-ff-total-adjoint", SOURCE_TOTAL),
        ("fixture-decision", FIXTURE_DECISION),
        ("fixture-manifest", FIXTURE_MANIFEST),
        ("fixture-guard", FIXTURE_GUARD),
        ("probe-source", PROBE_SOURCE),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"pre-FF normalization input drifted: {identifier}")
    decision = json.loads((PARENT_RESULT / "decision.json").read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    fixture = json.loads(FIXTURE_DECISION.read_text())
    if not (
        decision["promotionPass"] is False
        and decision["measurements"]["fusedTotalMismatchCount"] > 0
        and decision["measurements"]["preconvertedTotalMismatchCount"] > 0
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "refuted"
        and reflection["decision"]["verdict"] == "mutate"
        and fixture["promotionPass"] is True
        and fixture["measurements"]["fixtureRepeatByteIdentical"] is True
    ):
        raise ValueError("pre-FF normalization source antecedents are not satisfied")
    for path, expected in source_base.source_parent.source_capture.base.EXPECTED.items():
        if not path.is_file() or source_base.source_parent.sha256(path) != expected:
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
        raise ValueError("normalization-branch experiment identifies another candidate")
    if reference(experiment_path, "experiment") != {
        **json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]),
        "id": "experiment",
    }:
        raise ValueError("job and normalization-branch experiment differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("normalization-branch result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("normalization-branch work root was not fresh")
    scratch = WORK / "build"
    scratch.mkdir()
    executable, hook, build = compile_tools(scratch)
    captures = [WORK / "capture-a", WORK / "capture-b"]
    capture_base = source_base.source_parent.source_capture.base
    executions = [capture_base.capture(executable, hook, path) for path in captures]
    manifests = [capture_base.directory_manifest(path) for path in captures]
    parent_manifest = json.loads(FIXTURE_MANIFEST.read_text())
    identities = [fixture_identity(row, parent_manifest) for row in manifests]
    combined: list[dict[str, Path]] = []
    for label, directory in zip(("a", "b"), captures, strict=True):
        input_path = WORK / f"{label}-norm-input.bf16"
        adjoint_path = WORK / f"{label}-norm-branch-adjoint.bf16"
        combine_probe(directory, "input", input_path)
        combine_probe(directory, "adjoint", adjoint_path)
        combined.append({"input": input_path, "adjoint": adjoint_path})
    compare = source_base.source_parent.compare_bf16
    input_comparison = compare(combined[0]["input"], SOURCE_HIDDEN)
    open_comparison = compare(combined[0]["adjoint"], OPEN_BRANCH)
    total_comparison = compare(combined[0]["adjoint"], SOURCE_TOTAL)
    source_input = RESULT / "source-pre-ff-norm-input.bf16"
    source_adjoint = RESULT / "source-pre-ff-norm-branch-adjoint.bf16"
    shutil.copyfile(combined[0]["input"], source_input)
    shutil.copyfile(combined[0]["adjoint"], source_adjoint)
    repeat = (
        manifests[0]["aggregateSha256"] == manifests[1]["aggregateSha256"]
        and all(
            combined[0][name].read_bytes() == combined[1][name].read_bytes()
            for name in ("input", "adjoint")
        )
    )
    probe_exact = all(row["declaredProbePopulationExact"] for row in identities)
    non_probe_mismatches = sum(
        len(row["nonProbeMismatches"]) for row in identities
    )
    source_closure = RESULT / "incremental_source.tar.xz"
    source_package(source_closure)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(json.dumps({
        "build": build,
        "captureManifests": manifests,
        "executions": executions,
        "fixtureIdentity": identities,
        "inputComparison": list(input_comparison),
        "openBranchComparison": list(open_comparison),
        "totalAdjointComparison": list(total_comparison),
    }, indent=2, sort_keys=True) + "\n")
    shutil.rmtree(WORK)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "captureCount": len(captures),
        "sampleCount": SAMPLES,
        "inputElementCount": source_input.stat().st_size // 2,
        "adjointElementCount": source_adjoint.stat().st_size // 2,
        "sourceCaptureDeterministic": repeat,
        "declaredProbeFileCount": sum(
            row["declaredProbeFileCount"] for row in identities
        ),
        "declaredProbePopulationExact": probe_exact,
        "nonProbeFixtureMismatchCount": non_probe_mismatches,
        "inputMismatchCount": input_comparison[0],
        "openBranchMismatchCount": open_comparison[0],
        "maximumOpenBranchAbsoluteError": open_comparison[1],
        "totalAdjointControlMismatchCount": total_comparison[0],
        "adjointComparatorLive": source_adjoint.read_bytes()
        != bytes(source_adjoint.stat().st_size),
        "incrementalSourceBytes": source_closure.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    evaluate = source_base.source_parent.source_capture.open_parent.evaluate
    promotion = evaluate(experiment["promotionPredicates"], measurements)
    kill = evaluate(experiment["killPredicates"], measurements)
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
        "decision": "authorize-successor" if promotion_pass else "retire" if kill_pass else "retry",
        "artifacts": [
            reference(execution_path, "execution"),
            reference(source_input, "source-pre-ff-norm-input"),
            reference(source_adjoint, "source-pre-ff-norm-branch-adjoint"),
            reference(source_closure, "incremental-source-package"),
        ],
        "generatedUtc": dt.datetime.now(dt.timezone.utc).replace(
            microsecond=0
        ).isoformat(),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(output)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
