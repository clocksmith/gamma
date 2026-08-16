#!/usr/bin/env python3
"""Salvage the exact open pre-w_o evidence into a valid receipt."""

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
import nncp_libnc_ff1_bias_state_reduce_64_q0 as oracle
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_w_o_input_forward_64_q0_retry_v2"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_open_top_w_o_input_forward_64_q0_retry_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PREVALIDATION = PARENT_RESULT / "decision.prevalidation.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_ARTIFACT = PARENT_RESULT / "open-exact-w-o-input.bf16"
PARENT_SOURCE = PARENT_RESULT / "incremental_source.tar.xz"
PARENT_EXPERIMENT = ROOT / (
    "operations/adaptive/experiments/"
    "nncp_open_top_w_o_input_forward_64_q0_retry_v1.json"
)
PARENT_JOB = ROOT / (
    "operations/adaptive/failed/000_20260816T165727Z_496e36c06d.json"
)
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T165727Z_496e36c06d.json"
)
SOURCE_RESULT = ROOT / "results/nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1"
SOURCE_DECISION = SOURCE_RESULT / "decision.json"
SOURCE_INPUT = SOURCE_RESULT / "source-w-o-input.bf16"
SOURCE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T162351Z_97a6519638.json"
)
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_open_top_w_o_input_forward_64_q0_retry_v2_materializer.py"
)
DESCRIPTOR = PROGRAM / "program.py"
ELEMENTS = 64 * 32 * 1024
SOURCE_CEILING = 300_000


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
        ("parent-prevalidation-result", PREVALIDATION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-guard", PARENT_GUARD),
        ("parent-open-exact-w-o-input", PARENT_ARTIFACT),
        ("parent-incremental-source", PARENT_SOURCE),
        ("parent-experiment", PARENT_EXPERIMENT),
        ("parent-failed-job", PARENT_JOB),
        ("parent-failure-reflection", PARENT_REFLECTION),
        ("source-decision", SOURCE_DECISION),
        ("source-w-o-input", SOURCE_INPUT),
        ("source-reflection", SOURCE_REFLECTION),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"salvage input drifted: {identifier}")
    reflection = json.loads(PARENT_REFLECTION.read_text())
    source = json.loads(SOURCE_DECISION.read_text())
    source_reflection = json.loads(SOURCE_REFLECTION.read_text())
    if not (
        reflection["validity"]["classification"] == "implementation-failure"
        and reflection["hypothesis"]["verdict"] == "not-tested"
        and reflection["decision"]["verdict"] == "retry"
        and source["promotionPass"] is True
        and source["measurements"]["rawProbeTensorMismatchCount"] == 0
        and source_reflection["validity"]["valid"] is True
        and source_reflection["hypothesis"]["verdict"] == "supported"
    ):
        raise ValueError("receipt-only salvage antecedents are not satisfied")


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, MATERIALIZER)),
        DESCRIPTOR.resolve(),
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
        raise ValueError("receipt salvage source closure exceeds ceiling")


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
        raise ValueError("job and salvage bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("salvage result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("salvage work root is not fresh")

    prevalidation = json.loads(PREVALIDATION.read_text())
    execution = json.loads(PARENT_EXECUTION.read_text())
    guard = json.loads(PARENT_GUARD.read_text())
    job = json.loads(PARENT_JOB.read_text())
    parent_experiment = json.loads(PARENT_EXPERIMENT.read_text())
    independent = oracle.compare_bf16(PARENT_ARTIFACT, SOURCE_INPUT)
    population = execution.get("populationReceipts", [])
    promotion_rows = prevalidation.get("promotionPredicates", [])
    kill_rows = prevalidation.get("killPredicates", [])
    preserved_science_pass = (
        prevalidation.get("schema")
        == "gamma.enwiki9.adaptive-experiment-result.v1"
        and prevalidation.get("candidateId") == PARENT_ID
        and prevalidation.get("promotionPass") is True
        and prevalidation.get("killPass") is False
        and prevalidation.get("decision") == "authorize-attention-descent"
        and all(row.get("passed") is True for row in promotion_rows)
        and any(row.get("passed") is False for row in kill_rows)
        and prevalidation["measurements"]["treatmentSourceMismatchCount"] == 0
        and prevalidation["measurements"]["streamMajorControlMismatchCount"]
        > 0
    )
    replay_receipts_pass = (
        len(population) == 2
        and population[0]["aggregate"] == population[1]["aggregate"]
        and all(row["checkpoints"] == 640 for row in population)
        and all(row["mismatches"] == 0 for row in population)
        and all(row["maximum"] == 0.0 for row in population)
        and all(len(row["receipts"]) == 32 for row in population)
    )
    execution_comparisons_pass = (
        execution["comparisons"]["treatment"]["mismatchCount"] == 0
        and execution["comparisons"]["treatment"]["maximumAbsoluteError"] == 0.0
        and execution["comparisons"]["streamMajorControl"]["mismatchCount"]
        > 0
        and execution["forbiddenDynamicDependencies"] == []
    )
    resource_envelope_pass = (
        job["state"] == "failed"
        and job["returncode"] == 1
        and guard["status"] == "complete"
        and guard["returncode"] == 1
        and guard["rss_guard_exceeded"] is False
        and guard["official_decimal_memory_exceeded"] is False
        and guard["temporary_disk_guard_exceeded"] is False
        and guard["max_sampled_tree_rss_kib"] <= guard["limit_kib"]
        and guard["max_sampled_temporary_disk_bytes"]
        <= guard["temporary_disk_limit_bytes"]
    )
    parent_binding_pass = (
        prevalidation["experiment"] == reference(PARENT_EXPERIMENT)
        and prevalidation["objective"] == research_contracts.objective_binding()
        and parent_experiment["objectiveCreditBytes"] == 0
    )

    artifact = RESULT / "open-exact-w-o-input.bf16"
    shutil.copyfile(PARENT_ARTIFACT, artifact)
    artifact_copy_exact = (
        artifact.stat().st_size == ELEMENTS * 2
        and artifact.read_bytes() == PARENT_ARTIFACT.read_bytes()
    )
    incremental_source = RESULT / "incremental_source.tar.xz"
    source_package(incremental_source)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "independentSourceComparison": independent,
                "parentArtifact": reference(PARENT_ARTIFACT),
                "parentExecution": reference(PARENT_EXECUTION),
                "parentGuard": reference(PARENT_GUARD),
                "parentJob": reference(PARENT_JOB),
                "parentPrevalidationResult": reference(PREVALIDATION),
                "parentSourcePackage": reference(PARENT_SOURCE),
                "preservedPopulationAggregates": [
                    row["aggregate"] for row in population
                ],
                "salvageBoundary": "receipt-only; no forward recomputation",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    shutil.rmtree(WORK)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "parentBindingPass": parent_binding_pass,
        "preservedSciencePass": preserved_science_pass,
        "replayReceiptsPass": replay_receipts_pass,
        "executionComparisonsPass": execution_comparisons_pass,
        "resourceEnvelopePass": resource_envelope_pass,
        "preWOElementCount": artifact.stat().st_size // 2,
        "independentSourceMismatchCount": independent["mismatchCount"],
        "maximumIndependentAbsoluteError": independent["maximumAbsoluteError"],
        "streamMajorControlMismatchCount": execution["comparisons"][
            "streamMajorControl"
        ]["mismatchCount"],
        "artifactCopyExact": artifact_copy_exact,
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
        "promotionPass": promotion_pass,
        "killPass": kill_pass,
        "promotionPredicates": promotion,
        "killPredicates": kill,
        "measurements": measurements,
        "decision": "authorize-successor" if promotion_pass else "retire",
        "artifacts": [
            reference(execution_path, "execution"),
            reference(artifact, "open-exact-w-o-input"),
            reference(incremental_source, "incremental-source-package"),
        ],
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(output)
    return 0 if promotion_pass and not kill_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
