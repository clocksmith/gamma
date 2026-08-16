#!/usr/bin/env python3
"""Capture source pre-FF total, branch, and direct adjoints in one graph."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import lzma
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_v1 as total_parent
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_pre_ff_same_run_contributions_64_q0_v1"
PARENT_ID = "nncp_libnc_bf16_gradient_merge_64_q0_retry_v5"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_pre_ff_same_run_contributions_64_q0_v1_materializer.py"
)
PROBE_SOURCE = PROGRAM / "same_run_probe.c"
COMPOSER_SOURCE = PROGRAM / "compose_bf16.cpp"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T151453Z_cbf1bff98d.json"
)
TOTAL_RESULT = ROOT / (
    "results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2"
)
SOURCE_TOTAL = TOTAL_RESULT / "source-pre-ff-hidden-adjoint.bf16"
TOTAL_DECISION = TOTAL_RESULT / "decision.json"
BRANCH_RESULT = ROOT / (
    "results/nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v2"
)
SOURCE_BRANCH = BRANCH_RESULT / "source-pre-ff-norm-branch-adjoint.bf16"
BRANCH_DECISION = BRANCH_RESULT / "decision.json"
OPEN_DIRECT = ROOT / (
    "results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/"
    "open-final-norm-input-residual.bf16"
)
FIXTURE_ROOT = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
FIXTURE_DECISION = FIXTURE_ROOT / "decision.json"
FIXTURE_MANIFEST = FIXTURE_ROOT / "fixture-manifest.json"
FIXTURE_GUARD = FIXTURE_ROOT / "guard.json"
SOURCE_CEILING = 2_000_000
STATES = 64
STREAMS = 32
WIDTH = 1024
ELEMENTS = STATES * STREAMS * WIDTH
KINDS = ("input", "total", "branch", "direct")
DECLARATIONS = """static void gamma_same_run_input_dump(
    NCTensor *value, int layer, int state);
static NCTensor *gamma_same_run_total_attach(
    NCTensor *value, int layer, int state);
static NCTensor *gamma_same_run_branch_attach(
    NCTensor *value, int layer, int state);
static NCTensor *gamma_same_run_direct_attach(NCTensor *value, int state);
static int gamma_same_run_capture(
    void *opaque, NCTensor *gradient, NCTensor *column_index);

"""


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    return total_parent.reference(path, identifier or path.stem)


def execute(command: list[str], cwd: Path) -> dict[str, Any]:
    completed = subprocess.run(
        command, cwd=cwd, capture_output=True, check=False
    )
    receipt = {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.decode(errors="replace"),
        "stderr": completed.stderr.decode(errors="replace"),
    }
    if completed.returncode:
        raise RuntimeError(json.dumps(receipt, sort_keys=True))
    return receipt


def patch_teacher(source: str) -> str:
    capture = total_parent.source_parent.source_capture
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
        "        gamma_same_run_set_block(block_idx);\n",
    )
    source = capture.replace_once(
        source,
        "        ff_input = nc_dup_tensor(t0);\n"
        "        if (s->ln_flags & LN_PRE) {\n"
        "            t0 = layer_norm(t0, tl->ln_g2, tl->ln_b2, s->ln_flags);\n"
        "        }",
        "        gamma_same_run_input_dump(t0, layer_idx, output_index);\n"
        "        t0 = gamma_same_run_total_attach(\n"
        "            t0, layer_idx, output_index);\n"
        "        ff_input = nc_dup_tensor(t0);\n"
        "        if (s->ln_flags & LN_PRE) {\n"
        "            t0 = gamma_same_run_branch_attach(\n"
        "                t0, layer_idx, output_index);\n"
        "            t0 = layer_norm(t0, tl->ln_g2, tl->ln_b2, s->ln_flags);\n"
        "        }",
    )
    source = capture.replace_once(
        source,
        "    if (s->ln_flags & LN_FINAL) {\n"
        "        layer_input = layer_norm(layer_input, s->ln_g, s->ln_b, s->ln_flags);\n"
        "    }",
        "    if (s->ln_flags & LN_FINAL) {\n"
        "        layer_input = gamma_same_run_direct_attach(\n"
        "            layer_input, output_index);\n"
        "        layer_input = layer_norm(\n"
        "            layer_input, s->ln_g, s->ln_b, s->ln_flags);\n"
        "    }",
    )
    source = capture.replace_once(
        source,
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
        "    if (gamma_same_run_capture(opaque, yg, get_col_index))\n"
        "        return;\n"
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
    )
    return source


def compile_tools(scratch: Path) -> tuple[Path, Path, dict[str, Any]]:
    source_parent = total_parent.source_parent
    original = source_parent.patch_teacher
    source_parent.patch_teacher = patch_teacher
    try:
        return source_parent.compile_tools(scratch)
    finally:
        source_parent.patch_teacher = original


def expected_probe_paths() -> set[str]:
    return {
        f"same_run_{kind}_s{state:03d}.{extension}"
        for kind in KINDS
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
        if row["path"].startswith("same_run_")
    }
    parent_rows = {
        row["path"]: (row["bytes"], row["sha256"])
        for row in parent_manifest["fixture"]["files"]
    }
    observed_rows = {
        row["path"]: (row["bytes"], row["sha256"])
        for row in manifest["files"]
        if not row["path"].startswith("same_run_")
    }
    mismatches = sorted(
        path for path in set(parent_rows) | set(observed_rows)
        if parent_rows.get(path) != observed_rows.get(path)
    )
    return {
        "declaredProbeFileCount": len(probe),
        "declaredProbePopulationExact": probe == expected,
        "nonProbeMismatches": mismatches,
    }


def combine_probe(directory: Path, kind: str, output: Path) -> None:
    parse_meta = total_parent.source_parent.source_capture.parse_meta
    with output.open("wb") as destination:
        for state in range(STATES):
            stem = f"same_run_{kind}_s{state:03d}"
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
                raise ValueError(f"same-run {kind} state differs: {state}")
            with payload.open("rb") as source:
                shutil.copyfileobj(source, destination, 8 * 1024 * 1024)
    if output.stat().st_size != ELEMENTS * 2:
        raise ValueError(f"same-run {kind} geometry differs")


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, MATERIALIZER)),
        PROBE_SOURCE.resolve(),
        COMPOSER_SOURCE.resolve(),
        PROGRAM_DESCRIPTOR.resolve(),
        total_parent.source_parent.source_capture.FIXTURE_HOOK.resolve(),
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
        raise ValueError("same-run source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-decision", PARENT_RESULT / "decision.json"),
        ("parent-execution", PARENT_RESULT / "execution.json"),
        ("parent-guard", PARENT_RESULT / "guard.json"),
        ("parent-reflection", PARENT_REFLECTION),
        ("sealed-source-total", SOURCE_TOTAL),
        ("sealed-total-decision", TOTAL_DECISION),
        ("sealed-source-branch", SOURCE_BRANCH),
        ("sealed-branch-decision", BRANCH_DECISION),
        ("open-direct-adjoint", OPEN_DIRECT),
        ("fixture-decision", FIXTURE_DECISION),
        ("fixture-manifest", FIXTURE_MANIFEST),
        ("fixture-guard", FIXTURE_GUARD),
        ("probe-source", PROBE_SOURCE),
        ("composer-source", COMPOSER_SOURCE),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"same-run input drifted: {identifier}")
    parent = json.loads((PARENT_RESULT / "decision.json").read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    total = json.loads(TOTAL_DECISION.read_text())
    branch = json.loads(BRANCH_DECISION.read_text())
    fixture = json.loads(FIXTURE_DECISION.read_text())
    if not (
        parent["promotionPass"] is False
        and parent["measurements"]["minimumMergeMismatchCount"] == 3
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "refuted"
        and reflection["decision"]["verdict"] == "mutate"
        and total["promotionPass"] is True
        and branch["promotionPass"] is True
        and fixture["promotionPass"] is True
    ):
        raise ValueError("same-run antecedents are not satisfied")
    expected = total_parent.source_parent.source_capture.base.EXPECTED
    for path, digest in expected.items():
        if not path.is_file() or total_parent.source_parent.sha256(path) != digest:
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
        raise ValueError("same-run experiment identifies another candidate")
    if reference(experiment_path, "experiment") != {
        **json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]),
        "id": "experiment",
    }:
        raise ValueError("job and same-run experiment differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("same-run result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("same-run work root was not fresh")

    build_root = WORK / "build"
    build_root.mkdir()
    executable, hook, build = compile_tools(build_root)
    composer = WORK / "compose-bf16"
    composer_build = execute([
        os.environ.get("CXX", "c++"), "-std=c++20", "-O3", "-Wall",
        "-Wextra", str(COMPOSER_SOURCE), "-o", str(composer),
    ], ROOT)
    captures = [WORK / "capture-a", WORK / "capture-b"]
    capture_base = total_parent.source_parent.source_capture.base
    executions = [capture_base.capture(executable, hook, path) for path in captures]
    manifests = [capture_base.directory_manifest(path) for path in captures]
    parent_manifest = json.loads(FIXTURE_MANIFEST.read_text())
    identities = [fixture_identity(row, parent_manifest) for row in manifests]
    combined: list[dict[str, Path]] = []
    compositions: list[dict[str, Path]] = []
    composition_receipts = []
    for label, directory in zip(("a", "b"), captures, strict=True):
        current = {}
        for kind in KINDS:
            destination = WORK / f"{label}-{kind}.bf16"
            combine_probe(directory, kind, destination)
            current[kind] = destination
        composed = WORK / f"{label}-composed.bf16"
        negated = WORK / f"{label}-negated.bf16"
        composition_receipts.append(execute([
            str(composer), str(current["branch"]), str(current["direct"]),
            str(composed), str(negated),
        ], ROOT))
        combined.append(current)
        compositions.append({"composed": composed, "negated": negated})

    compare = total_parent.source_parent.compare_bf16
    comparisons = {
        "sealedTotal": compare(combined[0]["total"], SOURCE_TOTAL),
        "sealedBranch": compare(combined[0]["branch"], SOURCE_BRANCH),
        "openDirect": compare(combined[0]["direct"], OPEN_DIRECT),
        "composedTotal": compare(
            compositions[0]["composed"], combined[0]["total"]
        ),
        "negated": compare(compositions[0]["negated"], combined[0]["total"]),
    }
    replay = (
        manifests[0]["aggregateSha256"] == manifests[1]["aggregateSha256"]
        and all(
            combined[0][kind].read_bytes() == combined[1][kind].read_bytes()
            for kind in KINDS
        )
        and all(
            compositions[0][kind].read_bytes()
            == compositions[1][kind].read_bytes()
            for kind in ("composed", "negated")
        )
    )
    retained = {
        "same-run-input": RESULT / "same-run-pre-ff-input.bf16",
        "same-run-total": RESULT / "same-run-pre-ff-total-adjoint.bf16",
        "same-run-branch": RESULT / "same-run-pre-ff-branch-adjoint.bf16",
        "same-run-direct": RESULT / "same-run-pre-ff-direct-adjoint.bf16",
        "same-run-composed": RESULT / "same-run-pre-ff-composed-adjoint.bf16",
    }
    source_keys = {
        "same-run-input": combined[0]["input"],
        "same-run-total": combined[0]["total"],
        "same-run-branch": combined[0]["branch"],
        "same-run-direct": combined[0]["direct"],
        "same-run-composed": compositions[0]["composed"],
    }
    for identifier, destination in retained.items():
        shutil.copyfile(source_keys[identifier], destination)
    source_closure = RESULT / "incremental_source.tar.xz"
    source_package(source_closure)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(json.dumps({
        "build": build,
        "composerBuild": composer_build,
        "compositionExecutions": composition_receipts,
        "captureManifests": manifests,
        "comparisons": {key: list(value) for key, value in comparisons.items()},
        "executions": executions,
        "fixtureIdentity": identities,
    }, indent=2, sort_keys=True) + "\n")
    shutil.rmtree(WORK)

    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "captureCount": len(captures),
        "elementCount": ELEMENTS,
        "declaredProbeFileCount": sum(
            row["declaredProbeFileCount"] for row in identities
        ),
        "declaredProbePopulationExact": all(
            row["declaredProbePopulationExact"] for row in identities
        ),
        "nonProbeFixtureMismatchCount": sum(
            len(row["nonProbeMismatches"]) for row in identities
        ),
        "sealedTotalMismatchCount": comparisons["sealedTotal"][0],
        "sealedBranchMismatchCount": comparisons["sealedBranch"][0],
        "openDirectMismatchCount": comparisons["openDirect"][0],
        "maximumOpenDirectAbsoluteError": comparisons["openDirect"][1],
        "composedTotalMismatchCount": comparisons["composedTotal"][0],
        "maximumComposedTotalAbsoluteError": comparisons["composedTotal"][1],
        "negatedControlMismatchCount": comparisons["negated"][0],
        "sourceCaptureDeterministic": replay,
        "incrementalSourceBytes": source_closure.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    evaluate = total_parent.source_parent.source_capture.open_parent.evaluate
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
        "decision": (
            "authorize-successor" if promotion_pass
            else "retire" if kill_pass else "retry"
        ),
        "artifacts": [
            reference(execution_path, "execution"),
            *(reference(path, identifier) for identifier, path in retained.items()),
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
