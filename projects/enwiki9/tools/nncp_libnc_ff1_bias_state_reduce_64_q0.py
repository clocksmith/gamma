#!/usr/bin/env python3
"""Measure LibNC's state-panel FF1 bias-reduction arithmetic."""

from __future__ import annotations

import argparse
from array import array
import datetime as dt
import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_ff1_bias_state_reduce_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T104952Z_2204470800.json"
)
EXACT_RESIDUAL = PARENT_RESULT / "open-ff1-output-residual.bf16"
BASELINE_GRADIENT = PARENT_RESULT / "open-ff-bias1-19-gradient.bf16"
FIXTURE_ROOT = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
FIXTURE_DECISION = FIXTURE_ROOT / "decision.json"
FIXTURE_MANIFEST = FIXTURE_ROOT / "fixture-manifest.json"
COMPARATOR = FIXTURE_ROOT / "fixture/gradients/0005_ff_bias1_19.bin"
LIBNC = Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05/libnc.so")
LIBNC_INCLUDE = LIBNC.parent
EXPECTED_LIBNC_SHA256 = (
    "1836cdfde987885e542cb88847cc58c9abefb0ef59a511ea9540dcbe46ac6d3e"
)
EVALUATOR_SOURCE = PROGRAM / "ff1_bias_state_reduce.c"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_ff1_bias_state_reduce_64_q0_materializer.py"
)
FEATURES = 6144
STREAMS = 32
STATES = 64
ELEMENTS = FEATURES * STREAMS * STATES
SOURCE_CEILING = 500_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    resolved = path.resolve()
    if ROOT.resolve() not in resolved.parents or not resolved.is_file():
        raise ValueError(f"artifact is not a project file: {path}")
    record = {
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{sha256(resolved)}",
    }
    if identifier is not None:
        record["id"] = identifier
    return record


def execute(command: list[str], cwd: Path) -> dict[str, Any]:
    started = dt.datetime.now(dt.timezone.utc)
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    finished = dt.datetime.now(dt.timezone.utc)
    receipt = {
        "command": command,
        "cwd": cwd.relative_to(ROOT).as_posix() if cwd != ROOT else ".",
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "elapsedSeconds": (finished - started).total_seconds(),
    }
    if result.returncode != 0:
        raise RuntimeError(json.dumps(receipt, sort_keys=True))
    return receipt


def compare_bf16(left: Path, right: Path) -> dict[str, int | float]:
    left_words = array("H")
    right_words = array("H")
    left_words.frombytes(left.read_bytes())
    right_words.frombytes(right.read_bytes())
    if sys.byteorder != "little":
        left_words.byteswap()
        right_words.byteswap()
    if len(left_words) != len(right_words):
        raise ValueError("BF16 comparison geometry differs")
    mismatch = 0
    maximum = 0.0
    for left_word, right_word in zip(left_words, right_words):
        if left_word == right_word:
            continue
        mismatch += 1
        left_value = struct.unpack("<f", struct.pack("<I", left_word << 16))[0]
        right_value = struct.unpack("<f", struct.pack("<I", right_word << 16))[0]
        maximum = max(maximum, abs(left_value - right_value))
    return {"mismatchCount": mismatch, "maximumAbsoluteError": maximum}


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-decision", PARENT_DECISION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-guard", PARENT_GUARD),
        ("parent-reflection", PARENT_REFLECTION),
        ("source-exact-ff1-output-residual", EXACT_RESIDUAL),
        ("baseline-open-bias-gradient", BASELINE_GRADIENT),
        ("fixture-decision", FIXTURE_DECISION),
        ("fixture-manifest", FIXTURE_MANIFEST),
        ("retained-ff-bias1-19-gradient", COMPARATOR),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    parent_guard = json.loads(PARENT_GUARD.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    fixture = json.loads(FIXTURE_DECISION.read_text())
    if not (
        parent["promotionPass"] is False
        and parent["measurements"]["sourceFf2InputResidualMismatchCount"] == 0
        and parent["measurements"]["sourceGateAdjointMismatchCount"] == 0
        and parent["measurements"]["sourceValueAdjointMismatchCount"] == 0
        and parent["measurements"]["topFf1BiasMismatchCount"] == 4708
        and parent_guard["returncode"] == 0
        and parent_guard["rss_guard_exceeded"] is False
        and parent_guard["temporary_disk_guard_exceeded"] is False
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "refuted"
        and reflection["decision"]["verdict"] == "mutate"
        and fixture["measurements"]["fixtureComplete"] is True
    ):
        raise ValueError("FF1 bias state-reduction antecedents are not satisfied")


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
            info = archive.gettarinfo(
                str(member), arcname=member.relative_to(ROOT).as_posix()
            )
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = ""
            info.mode = 0o644
            with member.open("rb") as stream:
                archive.addfile(info, stream)
    path.write_bytes(lzma.compress(tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME))
    tar_path.unlink()
    if path.stat().st_size > SOURCE_CEILING:
        raise ValueError("FF1 bias state-reduction source closure exceeds ceiling")


def evaluate(predicates: list[dict[str, Any]], measurements: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for predicate in predicates:
        observed = measurements[predicate["measurement"]]
        operator = predicate["operator"]
        threshold = predicate["threshold"]
        if operator == "eq":
            passed = observed == threshold
        elif operator == "gt":
            passed = observed > threshold
        elif operator == "lte":
            passed = observed <= threshold
        else:
            raise ValueError(f"unsupported predicate operator: {operator}")
        rows.append({**predicate, "observed": observed, "passed": passed})
    return rows


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
        raise ValueError("job and FF1 bias experiment bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("FF1 bias result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("FF1 bias work root was not freshly materialized")
    if sha256(LIBNC) != EXPECTED_LIBNC_SHA256:
        raise ValueError("LibNC digest differs from attributed production library")

    build = WORK / "build"
    build.mkdir()
    evaluator = build / "ff1_bias_state_reduce"
    build_receipt = execute(
        [
            os.environ.get("CC", "cc"), "-std=gnu11", "-O2", "-Wall",
            "-Wextra", "-Werror", f"-I{LIBNC_INCLUDE}",
            str(EVALUATOR_SOURCE), str(LIBNC),
            f"-Wl,-rpath,{LIBNC_INCLUDE}", "-lm", "-lpthread", "-o",
            str(evaluator),
        ],
        ROOT,
    )
    ldd_receipt = execute(["ldd", str(evaluator)], ROOT)
    if str(LIBNC) not in ldd_receipt["stdout"]:
        raise ValueError("evaluator did not resolve the attributed LibNC")

    evaluations = []
    for replay in ("a", "b"):
        directory = WORK / replay
        directory.mkdir()
        outputs = {
            "treatment": directory / "treatment.bf16",
            "reverse": directory / "reverse.bf16",
            "negated": directory / "negated.bf16",
        }
        receipt = execute(
            [str(evaluator), str(EXACT_RESIDUAL), *(str(outputs[name]) for name in outputs)],
            WORK,
        )
        if any(path.stat().st_size != FEATURES * 2 for path in outputs.values()):
            raise ValueError("FF1 bias evaluator output geometry differs")
        evaluations.append(
            {
                "receipt": receipt,
                "outputs": outputs,
                "sha256": {name: sha256(path) for name, path in outputs.items()},
            }
        )
    replay_identical = evaluations[0]["sha256"] == evaluations[1]["sha256"]
    treatment_comparison = compare_bf16(evaluations[0]["outputs"]["treatment"], COMPARATOR)
    reverse_comparison = compare_bf16(evaluations[0]["outputs"]["reverse"], COMPARATOR)
    baseline_comparison = compare_bf16(BASELINE_GRADIENT, COMPARATOR)
    negated_comparison = compare_bf16(evaluations[0]["outputs"]["negated"], COMPARATOR)

    treatment_artifact = RESULT / "source-exact-ff-bias1-19-gradient.bf16"
    shutil.copyfile(evaluations[0]["outputs"]["treatment"], treatment_artifact)
    incremental_source = RESULT / "incremental_source.tar.xz"
    source_package(incremental_source)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "build": build_receipt,
                "ldd": ldd_receipt,
                "librarySha256": EXPECTED_LIBNC_SHA256,
                "sourceAttribution": {
                    "forwardOperation": "nc_add(matrix, nc_dup_tensor(ff_bias1))",
                    "backwardOperation": "nc_reduce_sum(existing_gradient, state_gradient, 1)",
                    "backwardDisassemblyRange": "libnc.so:0x76d6a-0x76d83",
                    "stateOrder": "chronological 0..63",
                    "statePanelShape": [FEATURES, STREAMS],
                    "stateReductionCallCount": STATES,
                },
                "evaluations": [
                    {"receipt": item["receipt"], "sha256": item["sha256"]}
                    for item in evaluations
                ],
                "comparisons": {
                    "treatment": treatment_comparison,
                    "reverse": reverse_comparison,
                    "baseline": baseline_comparison,
                    "negated": negated_comparison,
                },
            },
            indent=2,
            sort_keys=True,
        ) + "\n"
    )
    shutil.rmtree(WORK)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "featureCount": FEATURES,
        "streamCount": STREAMS,
        "stateCount": STATES,
        "inputElementCount": ELEMENTS,
        "stateReductionCallCount": STATES,
        "treatmentMismatchCount": treatment_comparison["mismatchCount"],
        "maximumTreatmentAbsoluteError": treatment_comparison["maximumAbsoluteError"],
        "baselineMismatchCount": baseline_comparison["mismatchCount"],
        "reverseMismatchCount": reverse_comparison["mismatchCount"],
        "negatedControlDiffers": negated_comparison["mismatchCount"] > 0,
        "evaluationReplayIdentical": replay_identical,
        "sourceLibraryDigestBound": True,
        "incrementalSourceBytes": incremental_source.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    promotion = evaluate(experiment["promotionPredicates"], measurements)
    kill = evaluate(experiment["killPredicates"], measurements)
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
        "decision": "authorize-successor" if promotion_pass else "retire" if kill_pass else "retry",
        "artifacts": [
            reference(execution_path, "execution"),
            reference(treatment_artifact, "source-exact-ff-bias1-19-gradient"),
            reference(incremental_source, "incremental-source-package"),
        ],
        "generatedUtc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(output)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
