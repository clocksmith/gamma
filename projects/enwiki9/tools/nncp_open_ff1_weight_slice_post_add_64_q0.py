#!/usr/bin/env python3
"""Confirm the immutable post-dot-add open FF1 weight-slice kernel."""

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
CANDIDATE_ID = "nncp_open_ff1_weight_slice_post_add_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_open_ff1_weight_slice_kernel_grid_64_q0_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T115801Z_99a2e7695e.json"
)
PARENT_SOURCE = ROOT / (
    "programs/nncp_open_ff1_weight_slice_kernel_grid_64_q0_v1/"
    "ff1_weight_slice_kernel_grid.cpp"
)
EXPECTED_PARENT_SHA256 = (
    "55c241191ceebbcc5d956ea781d79b4afaac470c0327dfef7fb44a7681278422"
)
SOURCE_PARENT_RESULT = ROOT / "results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1"
OPEN_INPUT = SOURCE_PARENT_RESULT / "open-ff1-input.bf16"
ORACLE_TREATMENT = SOURCE_PARENT_RESULT / "libnc-treatment-slice.bf16"
ORACLE_REVERSE = SOURCE_PARENT_RESULT / "libnc-reverse-control-slice.bf16"
ORACLE_NEGATED = SOURCE_PARENT_RESULT / "libnc-negated-control-slice.bf16"
RESIDUAL = ROOT / (
    "results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/"
    "open-ff1-output-residual.bf16"
)
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_open_ff1_weight_slice_post_add_64_q0_materializer.py"
)
SLICE_ELEMENTS = 128 * 1024
SOURCE_CEILING = 500_000

OLD_CALLS = """        write_words(argv[3], project(
            inputs, residuals, Mode::prior_fma, false, false));
        write_words(argv[4], project(
            inputs, residuals, Mode::post_add, false, false));
        write_words(argv[5], project(
            inputs, residuals, Mode::prior_nonfused, false, false));
        write_words(argv[6], project(
            inputs, residuals, Mode::prior_fma, true, false));
        write_words(argv[7], project(
            inputs, residuals, Mode::prior_fma, false, true));
"""
NEW_CALLS = """        write_words(argv[3], project(
            inputs, residuals, Mode::post_add, false, false));
        write_words(argv[4], project(
            inputs, residuals, Mode::prior_fma, false, false));
        write_words(argv[5], project(
            inputs, residuals, Mode::prior_nonfused, false, false));
        write_words(argv[6], project(
            inputs, residuals, Mode::post_add, true, false));
        write_words(argv[7], project(
            inputs, residuals, Mode::post_add, false, true));
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    return oracle.reference(path, identifier)


def derive_source(output: Path) -> dict[str, str | int]:
    if sha256(PARENT_SOURCE) != EXPECTED_PARENT_SHA256:
        raise ValueError("open FF1 weight-grid parent source digest differs")
    source = PARENT_SOURCE.read_text()
    if source.count(OLD_CALLS) != 1:
        raise ValueError("post-dot-add source boundary is not unique")
    source = source.replace(OLD_CALLS, NEW_CALLS)
    output.write_text(source)
    return {
        "parentSha256": EXPECTED_PARENT_SHA256,
        "derivedSha256": sha256(output),
        "replacementCount": 1,
    }


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-decision", PARENT_DECISION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-guard", PARENT_GUARD),
        ("parent-reflection", PARENT_REFLECTION),
        ("parent-evaluator-source", PARENT_SOURCE),
        ("open-ff1-input", OPEN_INPUT),
        ("source-exact-ff1-output-residual", RESIDUAL),
        ("libnc-treatment-slice", ORACLE_TREATMENT),
        ("libnc-reverse-control-slice", ORACLE_REVERSE),
        ("libnc-negated-control-slice", ORACLE_NEGATED),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    guard = json.loads(PARENT_GUARD.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    if not (
        parent["promotionPass"] is False
        and parent["killPass"] is True
        and parent["measurements"]["priorFmaMismatchCount"] == 43
        and parent["measurements"]["postAddMismatchCount"] == 0
        and parent["measurements"]["nonfusedMismatchCount"] == 43
        and parent["measurements"]["evaluationReplayIdentical"] is True
        and guard["returncode"] == 0
        and guard["rss_guard_exceeded"] is False
        and guard["temporary_disk_guard_exceeded"] is False
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "refuted"
        and reflection["decision"]["verdict"] == "mutate"
    ):
        raise ValueError("post-dot-add FF1 weight-slice antecedents are not satisfied")


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, MATERIALIZER)),
        PARENT_SOURCE.resolve(),
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
        raise ValueError("post-dot-add FF1 weight source closure exceeds ceiling")


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
        raise ValueError("job and post-dot-add experiment bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("post-dot-add result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("post-dot-add work root was not freshly materialized")

    build = WORK / "build"
    build.mkdir()
    derived_source = build / "ff1_weight_slice_post_add.cpp"
    derivation = derive_source(derived_source)
    evaluator = build / "ff1_weight_slice_post_add"
    build_receipt = oracle.execute(
        [
            os.environ.get("CXX", "g++"), "-std=c++17", "-O3", "-mavx2",
            "-mfma", "-ffp-contract=off", "-Wall", "-Wextra", "-Werror",
            str(derived_source), "-o", str(evaluator),
        ],
        ROOT,
    )
    build_receipt["sourceDerivation"] = derivation
    ldd_receipt = oracle.execute(["ldd", str(evaluator)], ROOT)
    forbidden = [
        line for line in ldd_receipt["stdout"].splitlines()
        if any(
            token in line.lower()
            for token in ("libnc", "ggml", "cuda", "openmp", "gomp", "blas")
        )
    ]

    output_names = ("treatment", "priorControl", "nonfused", "reverse", "negated")
    evaluations: list[dict[str, Any]] = []
    replay_paths: list[dict[str, Path]] = []
    for replay in ("a", "b"):
        directory = WORK / replay
        directory.mkdir()
        paths = {name: directory / f"{name}.bf16" for name in output_names}
        receipt = oracle.execute(
            [
                str(evaluator), str(OPEN_INPUT), str(RESIDUAL),
                *(str(paths[name]) for name in output_names),
            ],
            WORK,
        )
        if any(path.stat().st_size != SLICE_ELEMENTS * 2
               for path in paths.values()):
            raise ValueError("post-dot-add output geometry differs")
        evaluations.append(
            {
                "receipt": receipt,
                "sha256": {name: sha256(paths[name]) for name in output_names},
            }
        )
        replay_paths.append(paths)
    replay_identical = all(
        replay_paths[0][name].read_bytes() == replay_paths[1][name].read_bytes()
        for name in output_names
    )
    comparisons = {
        "treatment": oracle.compare_bf16(
            replay_paths[0]["treatment"], ORACLE_TREATMENT
        ),
        "priorControl": oracle.compare_bf16(
            replay_paths[0]["priorControl"], ORACLE_TREATMENT
        ),
        "nonfused": oracle.compare_bf16(
            replay_paths[0]["nonfused"], ORACLE_TREATMENT
        ),
        "reverse": oracle.compare_bf16(
            replay_paths[0]["reverse"], ORACLE_REVERSE
        ),
        "negated": oracle.compare_bf16(
            replay_paths[0]["negated"], ORACLE_NEGATED
        ),
    }
    artifacts = {
        "open-treatment-slice": RESULT / "open-treatment-slice.bf16",
        "open-prior-control-slice": RESULT / "open-prior-control-slice.bf16",
        "open-nonfused-control-slice": RESULT / "open-nonfused-control-slice.bf16",
        "open-reverse-slice": RESULT / "open-reverse-slice.bf16",
        "open-negated-slice": RESULT / "open-negated-slice.bf16",
    }
    for (identifier, destination), name in zip(artifacts.items(), output_names):
        shutil.copyfile(replay_paths[0][name], destination)
    incremental_source = RESULT / "incremental_source.tar.xz"
    source_package(incremental_source)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "arithmeticContract": {
                    "dot": "32 sequential AVX2 FMAs from zero",
                    "prior": "add decoded prior BF16 gradient after the dot",
                    "materialization": "round-to-nearest-even BF16 after each state",
                    "laneMapping": "eight adjacent FF1 output features",
                },
                "build": build_receipt,
                "comparisons": comparisons,
                "evaluations": evaluations,
                "forbiddenDynamicDependencies": forbidden,
                "ldd": ldd_receipt,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    shutil.rmtree(WORK)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "sliceElementCount": SLICE_ELEMENTS,
        "treatmentMismatchCount": comparisons["treatment"]["mismatchCount"],
        "maximumTreatmentAbsoluteError": comparisons["treatment"]["maximumAbsoluteError"],
        "priorControlMismatchCount": comparisons["priorControl"]["mismatchCount"],
        "nonfusedControlMismatchCount": comparisons["nonfused"]["mismatchCount"],
        "reverseOracleMismatchCount": comparisons["reverse"]["mismatchCount"],
        "negatedOracleMismatchCount": comparisons["negated"]["mismatchCount"],
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
            "authorize-successor" if promotion_pass
            else "retire" if kill_pass else "retry"
        ),
        "artifacts": [
            reference(execution_path, "execution"),
            *(reference(path, identifier) for identifier, path in artifacts.items()),
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
