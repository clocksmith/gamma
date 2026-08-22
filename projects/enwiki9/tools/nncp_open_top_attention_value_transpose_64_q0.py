#!/usr/bin/env python3
"""Validate the LibNC-free layer-19 value-attention transpose."""

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
CANDIDATE_ID = "nncp_open_top_attention_value_transpose_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_open_top_attention_forward_inputs_64_q0_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T220926Z_56872cd576.json"
)
VALUE_STATE = PARENT_RESULT / "open-exact-value-state.bf16"
SOURCE_ID = "nncp_libnc_top_attention_product_oracle_64_q0_retry_v2"
SOURCE_RESULT = ROOT / "results" / SOURCE_ID
SOURCE_DECISION = SOURCE_RESULT / "decision.json"
SOURCE_EXECUTION = SOURCE_RESULT / "execution.json"
SOURCE_GUARD = SOURCE_RESULT / "guard.json"
SOURCE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T174722Z_8b88b4a53d.json"
)
SOURCE_ADJOINT = SOURCE_RESULT / "source-attention-probability-adjoint.bf16"
CONCAT_ID = "nncp_open_concat_head_identity_64_q0_v1"
CONCAT_RESULT = ROOT / "results" / CONCAT_ID
CONCAT_DECISION = CONCAT_RESULT / "decision.json"
CONCAT_EXECUTION = CONCAT_RESULT / "execution.json"
CONCAT_GUARD = CONCAT_RESULT / "guard.json"
CONCAT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T175422Z_91aae07812.json"
)
ATTENDED_ADJOINT = CONCAT_RESULT / "open-exact-attended-adjoint.bf16"
PANEL_ID = "nncp_open_w_o_input_adjoint_block128_64_q0_v1"
PANEL_RESULT = ROOT / "results" / PANEL_ID
PANEL_DECISION = PANEL_RESULT / "decision.json"
PANEL_EXECUTION = PANEL_RESULT / "execution.json"
PANEL_GUARD = PANEL_RESULT / "guard.json"
PANEL_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T164348Z_ff5718724e.json"
)
EVALUATOR_SOURCE = PROGRAM / "attention_value_transpose.cpp"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_open_top_attention_value_transpose_64_q0_materializer.py"
)
STATES = 64
STREAMS = 32
HEADS = 8
KEYS = 320
HEAD_WIDTH = 128
ELEMENTS = STATES * HEADS * STREAMS * KEYS
SOURCE_CEILING = 500_000


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
        ("parent-decision", PARENT_DECISION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-guard", PARENT_GUARD),
        ("parent-reflection", PARENT_REFLECTION),
        ("open-value-state", VALUE_STATE),
        ("source-decision", SOURCE_DECISION),
        ("source-execution", SOURCE_EXECUTION),
        ("source-guard", SOURCE_GUARD),
        ("source-reflection", SOURCE_REFLECTION),
        ("source-probability-adjoint", SOURCE_ADJOINT),
        ("concat-decision", CONCAT_DECISION),
        ("concat-execution", CONCAT_EXECUTION),
        ("concat-guard", CONCAT_GUARD),
        ("concat-reflection", CONCAT_REFLECTION),
        ("open-attended-adjoint", ATTENDED_ADJOINT),
        ("panel-decision", PANEL_DECISION),
        ("panel-execution", PANEL_EXECUTION),
        ("panel-guard", PANEL_GUARD),
        ("panel-reflection", PANEL_REFLECTION),
        ("evaluator-source", EVALUATOR_SOURCE),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"attention transpose input drifted: {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    parent_reflection = json.loads(PARENT_REFLECTION.read_text())
    source = json.loads(SOURCE_DECISION.read_text())
    source_reflection = json.loads(SOURCE_REFLECTION.read_text())
    concat = json.loads(CONCAT_DECISION.read_text())
    concat_reflection = json.loads(CONCAT_REFLECTION.read_text())
    panel = json.loads(PANEL_DECISION.read_text())
    panel_reflection = json.loads(PANEL_REFLECTION.read_text())
    if not (
        parent["promotionPass"] is True
        and parent["measurements"]["valueStateElementCount"]
        == STREAMS * HEADS * KEYS * HEAD_WIDTH
        and parent["measurements"]["probabilitySourceMismatchCount"] == 0
        and parent_reflection["validity"]["valid"] is True
        and parent_reflection["hypothesis"]["verdict"] == "supported"
        and source["promotionPass"] is True
        and source["measurements"]["probabilityAdjointElementCount"] == ELEMENTS
        and source_reflection["validity"]["valid"] is True
        and source_reflection["hypothesis"]["verdict"] == "supported"
        and concat["promotionPass"] is True
        and concat["measurements"]["adjointMismatchCount"] == 0
        and concat_reflection["validity"]["valid"] is True
        and concat_reflection["hypothesis"]["verdict"] == "supported"
        and panel["promotionPass"] is True
        and panel["measurements"]["block128SourceMismatchCount"] == 0
        and panel_reflection["validity"]["valid"] is True
        and panel_reflection["hypothesis"]["verdict"] == "supported"
    ):
        raise ValueError("attention transpose antecedents are not satisfied")


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, MATERIALIZER)),
        EVALUATOR_SOURCE.resolve(),
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
        raise ValueError("attention transpose source closure exceeds ceiling")


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
        raise ValueError("job and attention transpose bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("attention transpose result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("attention transpose work root is not fresh")

    evaluator = WORK / "attention_value_transpose"
    build = oracle.execute(
        [
            os.environ.get("CXX", "g++"), "-std=c++17", "-O3", "-mavx2",
            "-mfma", "-ffp-contract=off", "-pthread", "-Wall", "-Wextra",
            "-Werror", str(EVALUATOR_SOURCE), "-o", str(evaluator),
        ],
        ROOT,
    )
    ldd = oracle.execute(["ldd", str(evaluator)], ROOT)
    forbidden = [
        line
        for line in ldd["stdout"].splitlines()
        if any(
            token in line.lower()
            for token in ("libnc", "ggml", "cuda", "openmp", "gomp", "blas")
        )
    ]
    output_names = ("treatment", "stream-major", "negated")
    evaluations: list[dict[str, Any]] = []
    replay_paths: list[dict[str, Path]] = []
    for replay in ("a", "b"):
        paths = {name: WORK / f"{name}-{replay}.bf16" for name in output_names}
        receipt = oracle.execute(
            [
                str(evaluator), str(VALUE_STATE), str(ATTENDED_ADJOINT),
                *(str(paths[name]) for name in output_names),
            ],
            WORK,
        )
        if any(path.stat().st_size != ELEMENTS * 2 for path in paths.values()):
            raise ValueError("attention transpose output geometry differs")
        evaluations.append(
            {
                "receipt": receipt,
                "sha256": {name: sha256(path) for name, path in paths.items()},
            }
        )
        replay_paths.append(paths)
    replay_identical = all(
        replay_paths[0][name].read_bytes() == replay_paths[1][name].read_bytes()
        for name in output_names
    )
    comparisons = {
        name: oracle.compare_bf16(replay_paths[0][name], SOURCE_ADJOINT)
        for name in output_names
    }
    artifact = RESULT / "source-exact-attention-probability-adjoint.bf16"
    shutil.copyfile(replay_paths[0]["treatment"], artifact)
    incremental_source = RESULT / "incremental_source.tar.xz"
    source_package(incremental_source)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "arithmeticContract": {
                    "operation": "dProbability = dAttended times value transpose",
                    "value": "stream-major, head-major, key-major, feature-major BF16",
                    "incoming": "state-major, stream-major, head-major, feature-major BF16",
                    "output": "state-major, head-major, stream-major, key-major BF16",
                    "laneMapping": "eight adjacent keys",
                    "reduction": "128 sequential AVX2 fused multiply-add steps from zero",
                    "materialization": "one final round-to-nearest-even BF16 conversion",
                },
                "build": build,
                "comparisons": comparisons,
                "evaluations": evaluations,
                "forbiddenDynamicDependencies": forbidden,
                "ldd": ldd,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    shutil.rmtree(WORK)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "sampleCount": STATES * STREAMS,
        "headCount": HEADS,
        "keyCount": KEYS,
        "reductionWidth": HEAD_WIDTH,
        "adjointElementCount": ELEMENTS,
        "treatmentMismatchCount": comparisons["treatment"]["mismatchCount"],
        "maximumTreatmentAbsoluteError": comparisons["treatment"][
            "maximumAbsoluteError"
        ],
        "streamMajorControlMismatchCount": comparisons["stream-major"][
            "mismatchCount"
        ],
        "negatedControlMismatchCount": comparisons["negated"]["mismatchCount"],
        "evaluationReplayIdentical": replay_identical,
        "forbiddenDynamicDependencyCount": len(forbidden),
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
            reference(artifact, "open-exact-attention-probability-adjoint"),
            reference(incremental_source, "incremental-source-package"),
        ],
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(output)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if promotion_pass and not kill_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
