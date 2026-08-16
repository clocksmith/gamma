#!/usr/bin/env python3
"""Capture both production layer-19 GEGLU branch adjoints."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shutil
from typing import Any

import nncp_libnc_top_ff2_input_adjoint_64_q0_v1 as parent
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_geglu_branch_adjoints_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
OPEN_ID = "nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v2"
OPEN_RESULT = ROOT / "results" / OPEN_ID
OPEN_DECISION = OPEN_RESULT / "decision.json"
OPEN_EXECUTION = OPEN_RESULT / "execution.json"
OPEN_GUARD = OPEN_RESULT / "guard.json"
OPEN_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T095147Z_8ddedba49c.json"
)
OPEN_FF1_RESIDUAL = OPEN_RESULT / "open-ff1-output-residual.bf16"
FIXTURE_ROOT = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
FIXTURE_DECISION = FIXTURE_ROOT / "decision.json"
FIXTURE_MANIFEST = FIXTURE_ROOT / "fixture-manifest.json"
FIXTURE_GUARD = FIXTURE_ROOT / "guard.json"
PROBE_SOURCE = ROOT / "tools/nncp_libnc_top_geglu_branch_probe_q0.c"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_top_geglu_branch_adjoints_64_q0_v1_materializer.py"
)
RUNNER = Path(__file__).resolve()
SOURCE_CEILING = 2_000_000
STATES = 64
STREAMS = 32
INNER = 3072
BRANCHES = ("gate", "value")
KINDS = ("input", "adjoint")
DECLARATIONS = """static void gamma_top_geglu_input_dump(
    NCTensor *value, int layer, int state, int branch);
static NCTensor *gamma_top_geglu_probe_attach(
    NCTensor *value, int layer, int state, int branch);
static int gamma_top_geglu_probe_capture(
    void *opaque, NCTensor *gradient, NCTensor *column_index);

"""


def patch_teacher(source: str) -> str:
    source = parent.capture.base.patch_teacher(source)
    source = parent.capture.replace_once(
        source,
        "static FILE *teacher_trace_file;\n",
        PROBE_SOURCE.read_text() + "\nstatic FILE *teacher_trace_file;\n",
    )
    source = parent.capture.replace_once(
        source,
        "static NCTensor *layer_norm(",
        DECLARATIONS + "static NCTensor *layer_norm(",
    )
    source = parent.capture.replace_once(
        source,
        "    while ((block_idx + n_states) <= block_stride) {\n"
        "        prof_start(PROF_TOTAL);\n",
        "    while ((block_idx + n_states) <= block_stride) {\n"
        "        prof_start(PROF_TOTAL);\n"
        "        gamma_top_geglu_probe_set_block(block_idx);\n",
    )
    source = parent.capture.replace_once(
        source,
        "                nc_split(tab2, t0, 2, NULL, 0);\n",
        "                nc_split(tab2, t0, 2, NULL, 0);\n"
        "                gamma_top_geglu_input_dump(\n"
        "                    tab2[0], layer_idx, output_index, 0);\n"
        "                gamma_top_geglu_input_dump(\n"
        "                    tab2[1], layer_idx, output_index, 1);\n"
        "                tab2[0] = gamma_top_geglu_probe_attach(\n"
        "                    tab2[0], layer_idx, output_index, 0);\n"
        "                tab2[1] = gamma_top_geglu_probe_attach(\n"
        "                    tab2[1], layer_idx, output_index, 1);\n",
    )
    source = parent.capture.replace_once(
        source,
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
        "    if (gamma_top_geglu_probe_capture(opaque, yg, get_col_index))\n"
        "        return;\n"
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
    )
    return source


def configure_parent() -> None:
    parent.CANDIDATE_ID = CANDIDATE_ID
    parent.PROGRAM = PROGRAM
    parent.RESULT = RESULT
    parent.WORK = WORK
    parent.PROBE_SOURCE = PROBE_SOURCE
    parent.PROGRAM_DESCRIPTOR = PROGRAM_DESCRIPTOR
    parent.MATERIALIZER = MATERIALIZER
    parent.RUNNER = RUNNER
    parent.SOURCE_CEILING = SOURCE_CEILING
    parent.patch_teacher = patch_teacher


def combine_probe(directory: Path, branch: str, kind: str, output: Path) -> None:
    with output.open("wb") as destination:
        for state in range(STATES):
            stem = f"top_geglu_{branch}_{kind}_s{state:03d}"
            payload = directory / f"{stem}.bin"
            metadata = directory / f"{stem}.meta"
            expected_meta = {
                "kind": kind,
                "branch": branch,
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
                or parent.capture.parse_meta(metadata) != expected_meta
            ):
                raise ValueError(
                    f"source GEGLU {branch} {kind} state differs: {state}"
                )
            with payload.open("rb") as source:
                shutil.copyfileobj(source, destination, 8 * 1024 * 1024)
    if output.stat().st_size != STATES * STREAMS * INNER * 2:
        raise ValueError(f"combined GEGLU {branch} {kind} geometry differs")


def split_open_residual(source: Path, gate: Path, value: Path) -> None:
    sample_bytes = 2 * INNER * 2
    if source.stat().st_size != STATES * STREAMS * sample_bytes:
        raise ValueError("open FF1-output residual geometry differs")
    with source.open("rb") as incoming, gate.open("wb") as gate_output, \
            value.open("wb") as value_output:
        for _sample in range(STATES * STREAMS):
            payload = incoming.read(sample_bytes)
            if len(payload) != sample_bytes:
                raise ValueError("open FF1-output residual is truncated")
            gate_output.write(payload[: 2 * INNER])
            value_output.write(payload[2 * INNER :])
        if incoming.read(1):
            raise ValueError("open FF1-output residual has trailing bytes")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("open-decision", OPEN_DECISION),
        ("open-execution", OPEN_EXECUTION),
        ("open-guard", OPEN_GUARD),
        ("open-reflection", OPEN_REFLECTION),
        ("open-ff1-output-residual", OPEN_FF1_RESIDUAL),
        ("production-fixture-decision", FIXTURE_DECISION),
        ("production-fixture-manifest", FIXTURE_MANIFEST),
        ("production-fixture-guard", FIXTURE_GUARD),
        ("probe-source", PROBE_SOURCE),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != parent.capture.reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    opened = json.loads(OPEN_DECISION.read_text())
    reflection = json.loads(OPEN_REFLECTION.read_text())
    guard = json.loads(OPEN_GUARD.read_text())
    fixture = json.loads(FIXTURE_DECISION.read_text())
    if not (
        opened["promotionPass"] is False
        and opened["killPass"] is True
        and opened["measurements"]["sourceFf2InputResidualMismatchCount"] == 0
        and opened["measurements"]["topFf1BiasMismatchCount"] == 4708
        and opened["measurements"]["openBackwardDeterministic"] is True
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "refuted"
        and reflection["decision"]["verdict"] == "mutate"
        and guard["returncode"] == 0
        and guard["rss_guard_exceeded"] is False
        and guard["temporary_disk_guard_exceeded"] is False
        and fixture["promotionPass"] is True
        and fixture["measurements"]["fixtureRepeatByteIdentical"] is True
        and fixture["measurements"]["targetBlockBefore"] == 256
    ):
        raise ValueError("source GEGLU branch antecedents are not satisfied")
    for path, expected in parent.capture.base.EXPECTED.items():
        if not path.is_file() or parent.capture.sha256(path) != expected:
            raise ValueError(f"frozen source input identity differs: {path}")


def main() -> int:
    configure_parent()
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
    if parent.capture.reference(experiment_path) != json.loads(
        os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]
    ):
        raise ValueError("job and GEGLU branch experiment bindings differ")
    candidate_revision = json.loads(
        os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"]
    )
    if candidate_revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("source GEGLU branch result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("source GEGLU branch work root was not freshly materialized")

    scratch = WORK / "build"
    scratch.mkdir()
    executable, hook, build = parent.compile_tools(scratch)
    capture_roots = [WORK / "capture-a", WORK / "capture-b"]
    executions = [
        parent.capture.base.capture(executable, hook, directory)
        for directory in capture_roots
    ]
    manifests = [
        parent.capture.base.directory_manifest(directory)
        for directory in capture_roots
    ]
    parent_manifest = json.loads(FIXTURE_MANIFEST.read_text())
    identities = [
        parent.capture.fixture_identity(manifest, parent_manifest)
        for manifest in manifests
    ]
    combined: list[dict[str, Path]] = []
    for label, directory in zip(("a", "b"), capture_roots, strict=True):
        current: dict[str, Path] = {}
        for branch in BRANCHES:
            for kind in KINDS:
                key = f"{branch}-{kind}"
                path = WORK / f"{label}-source-geglu-{key}.bf16"
                combine_probe(directory, branch, kind, path)
                current[key] = path
        combined.append(current)

    open_gate = WORK / "open-gate-adjoint.bf16"
    open_value = WORK / "open-value-adjoint.bf16"
    split_open_residual(OPEN_FF1_RESIDUAL, open_gate, open_value)
    comparisons = {
        "gate": parent.compare_bf16(combined[0]["gate-adjoint"], open_gate),
        "value": parent.compare_bf16(combined[0]["value-adjoint"], open_value),
    }
    artifacts: dict[str, Path] = {}
    for branch in BRANCHES:
        for kind in KINDS:
            key = f"{branch}-{kind}"
            path = RESULT / f"source-geglu-{key}.bf16"
            shutil.copyfile(combined[0][key], path)
            artifacts[key] = path
    repeat_identical = (
        manifests[0]["aggregateSha256"] == manifests[1]["aggregateSha256"]
        and all(
            combined[0][key].read_bytes() == combined[1][key].read_bytes()
            for key in combined[0]
        )
    )
    comparator_live = all(
        artifacts[f"{branch}-adjoint"].read_bytes()
        != bytes(artifacts[f"{branch}-adjoint"].stat().st_size)
        for branch in BRANCHES
    )
    fixture_identical = all(identity[0] for identity in identities)
    fixture_mismatch_count = sum(len(identity[1]) for identity in identities)
    source_closure = RESULT / "incremental_source.tar.xz"
    parent.source_package(source_closure)
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
                "openBranchComparisons": comparisons,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    shutil.rmtree(WORK)
    branch_elements = artifacts["gate-adjoint"].stat().st_size // 2
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "captureCount": len(capture_roots),
        "sampleCount": STATES * STREAMS,
        "branchInputElementCount": branch_elements,
        "branchAdjointElementCount": branch_elements,
        "sourceCaptureDeterministic": repeat_identical,
        "fixturePayloadIdentical": fixture_identical,
        "fixturePayloadMismatchCount": fixture_mismatch_count,
        "gateAdjointMismatchCount": comparisons["gate"][0],
        "maximumGateAdjointAbsoluteError": comparisons["gate"][1],
        "valueAdjointMismatchCount": comparisons["value"][0],
        "maximumValueAdjointAbsoluteError": comparisons["value"][1],
        "anyBranchAdjointMismatch": any(value[0] > 0 for value in comparisons.values()),
        "comparatorLive": comparator_live,
        "incrementalSourceBytes": source_closure.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    promotion = parent.capture.open_parent.evaluate(
        experiment["promotionPredicates"], measurements
    )
    kill = parent.capture.open_parent.evaluate(
        experiment["killPredicates"], measurements
    )
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": research_contracts.objective_binding(),
        "experiment": parent.capture.reference(experiment_path),
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
            parent.capture.reference(execution_path, "execution"),
            *(
                parent.capture.reference(path, f"source-geglu-{key}")
                for key, path in sorted(artifacts.items())
            ),
            parent.capture.reference(source_closure, "incremental-source-package"),
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
