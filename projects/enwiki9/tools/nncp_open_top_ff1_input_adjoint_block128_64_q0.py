#!/usr/bin/env python3
"""Test the open ordered-panel top-FF1 input-adjoint transpose."""

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
CANDIDATE_ID = "nncp_open_top_ff1_input_adjoint_block128_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_libnc_top_ff1_input_adjoint_64_q0_retry_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T123446Z_5cbfc56c6d.json"
)
SOURCE_ADJOINT = PARENT_RESULT / "source-ff1-input-adjoint.bf16"
WEIGHTS = PARENT_RESULT / "source-initial-ff1-19.bf16"
INCOMING = ROOT / (
    "results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/"
    "open-ff1-output-residual.bf16"
)
FF2_RESULT = ROOT / "results/nncp_libnc_ff2_transpose_block128_64_q0_v1"
FF2_DECISION = FF2_RESULT / "decision.json"
FF2_EXECUTION = FF2_RESULT / "execution.json"
FF2_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T093907Z_7f51e2d346.json"
)
EVALUATOR_SOURCE = PROGRAM / "ff1_transpose_block128.cpp"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_open_top_ff1_input_adjoint_block128_64_q0_materializer.py"
)
ELEMENTS = 64 * 32 * 1024
SOURCE_CEILING = 1_000_000


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
        ("source-ff1-input-adjoint", SOURCE_ADJOINT),
        ("source-initial-ff1-19", WEIGHTS),
        ("open-ff1-output-adjoint", INCOMING),
        ("ff2-panel-decision", FF2_DECISION),
        ("ff2-panel-execution", FF2_EXECUTION),
        ("ff2-panel-reflection", FF2_REFLECTION),
        ("evaluator-source", EVALUATOR_SOURCE),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    guard = json.loads(PARENT_GUARD.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    ff2 = json.loads(FF2_DECISION.read_text())
    ff2_reflection = json.loads(FF2_REFLECTION.read_text())
    if not (
        parent["promotionPass"] is True
        and parent["killPass"] is False
        and parent["measurements"]["sourceInputMismatchCount"] == 0
        and parent["measurements"]["sourceCaptureDeterministic"] is True
        and parent["measurements"]["comparatorLive"] is True
        and parent["measurements"]["fixturePayloadMismatchCount"] == 0
        and parent["measurements"]["declaredProbePopulationExact"] is True
        and guard["returncode"] == 0
        and guard["rss_guard_exceeded"] is False
        and guard["temporary_disk_guard_exceeded"] is False
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "supported"
        and reflection["decision"]["verdict"] == "mutate"
        and ff2["promotionPass"] is True
        and ff2["measurements"]["block128SourceMismatchCount"] == 0
        and ff2_reflection["validity"]["valid"] is True
        and ff2_reflection["hypothesis"]["verdict"] == "supported"
    ):
        raise ValueError("open FF1 transpose antecedents are not satisfied")


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
        raise ValueError("open FF1 transpose source closure exceeds ceiling")


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
        raise ValueError("job and open FF1 transpose bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("open FF1 transpose result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("open FF1 transpose work root was not freshly materialized")

    evaluator = WORK / "ff1_transpose_block128"
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
    evaluations: list[dict[str, Any]] = []
    paths: list[dict[str, Path]] = []
    for replay in ("a", "b"):
        outputs = {
            "block128": WORK / f"block128-{replay}.bf16",
            "unblocked": WORK / f"unblocked-{replay}.bf16",
        }
        receipt = oracle.execute(
            [
                str(evaluator), str(WEIGHTS), str(INCOMING),
                str(outputs["block128"]), str(outputs["unblocked"]),
            ],
            WORK,
        )
        if any(path.stat().st_size != ELEMENTS * 2 for path in outputs.values()):
            raise ValueError("open FF1 transpose output geometry differs")
        evaluations.append(
            {
                "receipt": receipt,
                "sha256": {name: sha256(path) for name, path in outputs.items()},
            }
        )
        paths.append(outputs)
    replay_identical = all(
        paths[0][name].read_bytes() == paths[1][name].read_bytes()
        for name in paths[0]
    )
    comparisons = {
        name: oracle.compare_bf16(paths[0][name], SOURCE_ADJOINT)
        for name in paths[0]
    }
    cells_differ = paths[0]["block128"].read_bytes() != paths[0][
        "unblocked"
    ].read_bytes()
    artifact = RESULT / "source-exact-ff1-input-adjoint.bf16"
    shutil.copyfile(paths[0]["block128"], artifact)
    incremental_source = RESULT / "incremental_source.tar.xz"
    source_package(incremental_source)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "arithmeticContract": {
                    "matrix": "initial BF16 ff1_19 transposed",
                    "incoming": "exact BF16 FF1 output adjoint",
                    "laneMapping": "eight adjacent FF1 input features",
                    "reduction": "48 ordered 128-output-feature panels",
                    "panelAccumulation": "sequential AVX2 FMAs from zero",
                    "panelCombination": "add each completed panel to the total",
                    "materialization": "one final round-to-nearest-even BF16 conversion",
                },
                "build": build,
                "cellsDiffer": cells_differ,
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
        "adjointElementCount": ELEMENTS,
        "reductionPanelCount": 48,
        "block128SourceMismatchCount": comparisons["block128"]["mismatchCount"],
        "maximumBlock128AbsoluteError": comparisons["block128"]["maximumAbsoluteError"],
        "unblockedSourceMismatchCount": comparisons["unblocked"]["mismatchCount"],
        "arithmeticCellsDiffer": cells_differ,
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
            reference(artifact, "source-exact-ff1-input-adjoint"),
            reference(incremental_source, "incremental-source-package"),
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
