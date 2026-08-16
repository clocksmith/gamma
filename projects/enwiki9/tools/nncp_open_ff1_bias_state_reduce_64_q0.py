#!/usr/bin/env python3
"""Measure LibNC-free FF1 bias state-boundary reduction."""

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
import nncp_libnc_ff1_bias_state_reduce_64_q0 as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_ff1_bias_state_reduce_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_libnc_ff1_bias_state_reduce_64_q0_retry_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T111831Z_64dcc1173e.json"
)
EXACT_RESIDUAL = ROOT / (
    "results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/"
    "open-ff1-output-residual.bf16"
)
ORACLE = PARENT_RESULT / "source-exact-ff-bias1-19-gradient.bf16"
BASELINE = ROOT / (
    "results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/"
    "open-ff-bias1-19-gradient.bf16"
)
EVALUATOR_SOURCE = PROGRAM / "ff1_bias_state_reduce.cpp"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / "tools/nncp_open_ff1_bias_state_reduce_64_q0_materializer.py"
FEATURES = 6144
ELEMENTS = 64 * 32 * FEATURES
SOURCE_CEILING = 500_000
VARIANTS = ("treatment", "flat", "reverse", "negated")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-decision", PARENT_DECISION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-guard", PARENT_GUARD),
        ("parent-reflection", PARENT_REFLECTION),
        ("source-exact-ff1-output-residual", EXACT_RESIDUAL),
        ("independent-bias-gradient-oracle", ORACLE),
        ("flattened-baseline-gradient", BASELINE),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != base.reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    decision = json.loads(PARENT_DECISION.read_text())
    guard = json.loads(PARENT_GUARD.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    if not (
        decision["promotionPass"] is True
        and decision["measurements"]["treatmentMismatchCount"] == 0
        and decision["measurements"]["baselineMismatchCount"] == 4708
        and decision["measurements"]["reverseMismatchCount"] == 5099
        and decision["measurements"]["evaluationReplayIdentical"] is True
        and guard["returncode"] == 0
        and guard["rss_guard_exceeded"] is False
        and guard["temporary_disk_guard_exceeded"] is False
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "supported"
        and reflection["decision"]["verdict"] == "mutate"
    ):
        raise ValueError("open FF1 bias reduction antecedents are not satisfied")


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, MATERIALIZER)),
        EVALUATOR_SOURCE.resolve(),
        PROGRAM_DESCRIPTOR.resolve(),
    ]
    members = sorted(set(members), key=lambda item: item.relative_to(ROOT).as_posix())
    tar_path = path.with_suffix("")
    with tarfile.open(tar_path, "w") as archive:
        for member in members:
            info = archive.gettarinfo(str(member), arcname=member.relative_to(ROOT).as_posix())
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = ""
            info.mode = 0o644
            with member.open("rb") as stream:
                archive.addfile(info, stream)
    path.write_bytes(lzma.compress(tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME))
    tar_path.unlink()
    if path.stat().st_size > SOURCE_CEILING:
        raise ValueError("open FF1 bias source closure exceeds ceiling")


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
    if base.reference(experiment_path) != json.loads(
        os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]
    ):
        raise ValueError("job and open FF1 bias experiment bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("open FF1 bias result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("open FF1 bias work root was not freshly materialized")

    build = WORK / "build"
    build.mkdir()
    evaluator = build / "ff1_bias_state_reduce"
    build_receipt = base.execute(
        [
            os.environ.get("CXX", "g++"), "-std=c++17", "-O3",
            "-ffp-contract=off", "-Wall", "-Wextra", "-Werror",
            str(EVALUATOR_SOURCE), "-o", str(evaluator),
        ],
        ROOT,
    )
    ldd_receipt = base.execute(["ldd", str(evaluator)], ROOT)
    forbidden = [
        line for line in ldd_receipt["stdout"].splitlines()
        if any(token in line.lower() for token in ("libnc", "ggml", "blas", "gomp", "openmp"))
    ]
    evaluations = []
    for replay in ("a", "b"):
        directory = WORK / replay
        directory.mkdir()
        files = {name: directory / f"{name}.bf16" for name in VARIANTS}
        receipt = base.execute(
            [str(evaluator), str(EXACT_RESIDUAL), *(str(files[name]) for name in VARIANTS)],
            WORK,
        )
        if any(path.stat().st_size != FEATURES * 2 for path in files.values()):
            raise ValueError("open FF1 bias output geometry differs")
        evaluations.append({
            "receipt": receipt,
            "files": files,
            "sha256": {name: base.sha256(path) for name, path in files.items()},
        })
    replay_identical = evaluations[0]["sha256"] == evaluations[1]["sha256"]
    comparisons = {
        name: base.compare_bf16(evaluations[0]["files"][name], ORACLE)
        for name in VARIANTS
    }
    baseline_identity = evaluations[0]["files"]["flat"].read_bytes() == BASELINE.read_bytes()
    treatment_artifact = RESULT / "open-source-exact-ff-bias1-19-gradient.bf16"
    shutil.copyfile(evaluations[0]["files"]["treatment"], treatment_artifact)
    incremental_source = RESULT / "incremental_source.tar.xz"
    source_package(incremental_source)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(json.dumps({
        "build": build_receipt,
        "ldd": ldd_receipt,
        "forbiddenDynamicDependencies": forbidden,
        "arithmeticContract": {
            "streamOrder": "0..31 sequential float32 adds",
            "stateOrder": "0..63 chronological",
            "materialization": "round-to-nearest-even BF16 after every state",
            "priorGradient": "decode prior state BF16 word before the next panel",
        },
        "evaluations": [
            {"receipt": item["receipt"], "sha256": item["sha256"]}
            for item in evaluations
        ],
        "comparisons": comparisons,
        "flatBaselineByteIdentical": baseline_identity,
    }, indent=2, sort_keys=True) + "\n")
    shutil.rmtree(WORK)
    treatment = comparisons["treatment"]
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "inputElementCount": ELEMENTS,
        "outputElementCount": FEATURES,
        "treatmentMismatchCount": treatment["mismatchCount"],
        "maximumTreatmentAbsoluteError": treatment["maximumAbsoluteError"],
        "flatMismatchCount": comparisons["flat"]["mismatchCount"],
        "reverseMismatchCount": comparisons["reverse"]["mismatchCount"],
        "negatedControlDiffers": comparisons["negated"]["mismatchCount"] > 0,
        "flatBaselineByteIdentical": baseline_identity,
        "evaluationReplayIdentical": replay_identical,
        "forbiddenDynamicDependencyCount": len(forbidden),
        "incrementalSourceBytes": incremental_source.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    promotion = base.evaluate(experiment["promotionPredicates"], measurements)
    kill = base.evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": research_contracts.objective_binding(),
        "experiment": base.reference(experiment_path),
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
            base.reference(execution_path, "execution"),
            base.reference(treatment_artifact, "open-source-exact-ff-bias1-19-gradient"),
            base.reference(incremental_source, "incremental-source-package"),
        ],
        "generatedUtc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(output)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
