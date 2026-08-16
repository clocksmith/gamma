#!/usr/bin/env python3
"""Validate the complete open post-dot-add layer-19 w_o gradient."""

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
CANDIDATE_ID = "nncp_open_w_o_gradient_full_post_add_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_open_w_o_weight_slice_post_add_64_q0_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T163008Z_9e18c10ab5.json"
)
SOURCE_RESULT = ROOT / "results/nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1"
SOURCE_INPUT = SOURCE_RESULT / "source-w-o-input.bf16"
UPSTREAM_RESULT = ROOT / "results/nncp_open_top_pre_ff_total_adjoint_64_q0_retry_v1"
UPSTREAM_ADJOINT = UPSTREAM_RESULT / "source-exact-pre-ff-total-adjoint.bf16"
RETAINED_GRADIENT = ROOT / (
    "results/nncp_libnc_profile_update_fixture_64_q3_v1/fixture/"
    "gradients/0007_w_o_19.bin"
)
RETAINED_GRADIENT_META = ROOT / (
    "results/nncp_libnc_profile_update_fixture_64_q3_v1/fixture/"
    "gradients/0007_w_o_19.meta"
)
EVALUATOR_SOURCE = PROGRAM / "w_o_gradient_full_post_add.cpp"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_open_w_o_gradient_full_post_add_64_q0_materializer.py"
)
ELEMENTS = 1024 * 1024
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
        ("source-w-o-input", SOURCE_INPUT),
        ("open-post-w-o-adjoint", UPSTREAM_ADJOINT),
        ("retained-w-o-gradient", RETAINED_GRADIENT),
        ("retained-w-o-gradient-meta", RETAINED_GRADIENT_META),
        ("evaluator-source", EVALUATOR_SOURCE),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    guard = json.loads(PARENT_GUARD.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    if not (
        parent["promotionPass"] is True
        and parent["measurements"]["treatmentMismatchCount"] == 0
        and parent["measurements"]["sliceElementCount"] == 131072
        and parent["measurements"]["evaluationReplayIdentical"] is True
        and parent["measurements"]["reverseControlMismatchCount"] > 0
        and parent["measurements"]["negatedControlMismatchCount"] > 0
        and guard["returncode"] == 0
        and guard["rss_guard_exceeded"] is False
        and guard["temporary_disk_guard_exceeded"] is False
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "supported"
        and reflection["decision"]["verdict"] == "mutate"
    ):
        raise ValueError("full open w_o gradient antecedents are not satisfied")


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
        raise ValueError("full open w_o gradient source closure exceeds ceiling")


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
        raise ValueError("job and full open w_o gradient bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("full open w_o gradient result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("full open w_o gradient work root is not fresh")

    evaluator = WORK / "w_o_gradient_full_post_add"
    build = oracle.execute(
        [
            os.environ.get("CXX", "g++"), "-std=c++17", "-O3", "-mavx2",
            "-mfma", "-ffp-contract=off", "-Wall", "-Wextra", "-Werror",
            str(EVALUATOR_SOURCE), "-o", str(evaluator),
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
    replay_paths: list[dict[str, Path]] = []
    for replay in ("a", "b"):
        paths = {
            "treatment": WORK / f"treatment-{replay}.bf16",
            "negated": WORK / f"negated-{replay}.bf16",
        }
        receipt = oracle.execute(
            [
                str(evaluator), str(SOURCE_INPUT), str(UPSTREAM_ADJOINT),
                str(paths["treatment"]), str(paths["negated"]),
            ],
            WORK,
        )
        if any(path.stat().st_size != ELEMENTS * 2 for path in paths.values()):
            raise ValueError("full open w_o gradient output geometry differs")
        evaluations.append(
            {
                "receipt": receipt,
                "sha256": {name: sha256(path) for name, path in paths.items()},
            }
        )
        replay_paths.append(paths)
    replay_identical = all(
        replay_paths[0][name].read_bytes() == replay_paths[1][name].read_bytes()
        for name in replay_paths[0]
    )
    treatment = oracle.compare_bf16(
        replay_paths[0]["treatment"], RETAINED_GRADIENT
    )
    negated = oracle.compare_bf16(replay_paths[0]["negated"], RETAINED_GRADIENT)
    artifact = RESULT / "source-exact-w-o-19-gradient.bf16"
    shutil.copyfile(replay_paths[0]["treatment"], artifact)
    incremental_source = RESULT / "incremental_source.tar.xz"
    source_package(incremental_source)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "arithmeticContract": {
                    "dot": "32 sequential AVX2 FMAs from zero",
                    "prior": "add decoded prior BF16 gradient after the dot",
                    "stateOrder": "0..63 chronological",
                    "materialization": "round-to-nearest-even BF16 after each state",
                    "coverage": "all 1,024 input by 1,024 output features",
                },
                "build": build,
                "comparisons": {"treatment": treatment, "negated": negated},
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
        "gradientElementCount": ELEMENTS,
        "treatmentMismatchCount": treatment["mismatchCount"],
        "maximumTreatmentAbsoluteError": treatment["maximumAbsoluteError"],
        "negatedControlMismatchCount": negated["mismatchCount"],
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
            reference(artifact, "source-exact-w-o-19-gradient"),
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
