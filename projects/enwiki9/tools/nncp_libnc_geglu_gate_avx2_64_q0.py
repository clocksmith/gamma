#!/usr/bin/env python3
"""Evaluate the disassembly-derived AVX2 GEGLU gate backward."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_geglu_gate_avx2_64_q0_v1"
PARENT_ID = "nncp_libnc_top_geglu_branch_adjoints_64_q0_retry_v2"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T102756Z_33b5fb91aa.json"
)
SOURCE_GATE_INPUT = PARENT_RESULT / "source-geglu-gate-input.bf16"
SOURCE_GATE_ADJOINT = PARENT_RESULT / "source-geglu-gate-adjoint.bf16"
SOURCE_VALUE_INPUT = PARENT_RESULT / "source-geglu-value-input.bf16"
SOURCE_VALUE_ADJOINT = PARENT_RESULT / "source-geglu-value-adjoint.bf16"
OPEN_ID = "nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v2"
OPEN_RESULT = ROOT / "results" / OPEN_ID
OPEN_DECISION = OPEN_RESULT / "decision.json"
OPEN_EXECUTION = OPEN_RESULT / "execution.json"
OPEN_GUARD = OPEN_RESULT / "guard.json"
OPEN_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T095147Z_8ddedba49c.json"
)
OPEN_FF2_RESIDUAL = OPEN_RESULT / "open-ff2-input-residual.bf16"
OPEN_FF1_RESIDUAL = OPEN_RESULT / "open-ff1-output-residual.bf16"
EVALUATOR_SOURCE = PROGRAM / "geglu_gate_avx2.cpp"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / "tools/nncp_libnc_geglu_gate_avx2_64_q0_materializer.py"
LIBNC = Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05/libnc.so")
EXPECTED_LIBNC_SHA256 = (
    "1836cdfde987885e542cb88847cc58c9abefb0ef59a511ea9540dcbe46ac6d3e"
)
KERNEL_START = 0x29850
KERNEL_END = 0x2999F
EXPECTED_KERNEL_SHA256 = (
    "c1714b34c9f4584240784d38d4e74b503007d0054fddc3770865cef4d3d11d9e"
)
ELEMENTS = 64 * 32 * 3072
INNER = 3072
SAMPLES = 64 * 32
SOURCE_CEILING = 1_000_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path: Path, identifier: str = "experiment") -> dict[str, str]:
    resolved = path.resolve()
    if ROOT.resolve() not in resolved.parents or not resolved.is_file():
        raise ValueError(f"experiment input is not a project file: {path}")
    return {
        "id": identifier,
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{sha256(resolved)}",
    }


def execute(command: list[str], cwd: Path) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    receipt = {
        "argv": command,
        "cwd": cwd.relative_to(ROOT).as_posix(),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if completed.returncode != 0:
        raise RuntimeError(json.dumps(receipt, sort_keys=True))
    return receipt


def compare_bf16(left: Path, right: Path) -> dict[str, int | float]:
    left_bytes = left.read_bytes()
    right_bytes = right.read_bytes()
    if len(left_bytes) != len(right_bytes) or len(left_bytes) % 2:
        raise ValueError("GEGLU BF16 comparison geometry differs")
    mismatches = 0
    maximum = 0.0
    for index in range(0, len(left_bytes), 2):
        left_word = int.from_bytes(left_bytes[index : index + 2], "little")
        right_word = int.from_bytes(right_bytes[index : index + 2], "little")
        if left_word == right_word:
            continue
        mismatches += 1
        left_value = struct.unpack("<f", struct.pack("<I", left_word << 16))[0]
        right_value = struct.unpack("<f", struct.pack("<I", right_word << 16))[0]
        maximum = max(maximum, abs(left_value - right_value))
    return {"mismatchCount": mismatches, "maximumAbsoluteError": maximum}


def split_open_residual(source: Path, gate: Path, value: Path) -> None:
    sample_bytes = 2 * INNER * 2
    if source.stat().st_size != SAMPLES * sample_bytes:
        raise ValueError("open FF1-output residual geometry differs")
    with source.open("rb") as incoming, gate.open("wb") as gate_output, \
            value.open("wb") as value_output:
        for _sample in range(SAMPLES):
            payload = incoming.read(sample_bytes)
            if len(payload) != sample_bytes:
                raise ValueError("open FF1-output residual is truncated")
            gate_output.write(payload[: 2 * INNER])
            value_output.write(payload[2 * INNER :])
        if incoming.read(1):
            raise ValueError("open FF1-output residual has trailing bytes")


def require_inputs(experiment: dict[str, Any]) -> tuple[bool, bool]:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-decision", PARENT_DECISION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-guard", PARENT_GUARD),
        ("parent-reflection", PARENT_REFLECTION),
        ("source-geglu-gate-input", SOURCE_GATE_INPUT),
        ("source-geglu-gate-adjoint", SOURCE_GATE_ADJOINT),
        ("source-geglu-value-input", SOURCE_VALUE_INPUT),
        ("source-geglu-value-adjoint", SOURCE_VALUE_ADJOINT),
        ("open-decision", OPEN_DECISION),
        ("open-execution", OPEN_EXECUTION),
        ("open-guard", OPEN_GUARD),
        ("open-reflection", OPEN_REFLECTION),
        ("open-ff2-input-residual", OPEN_FF2_RESIDUAL),
        ("open-ff1-output-residual", OPEN_FF1_RESIDUAL),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    parent_reflection = json.loads(PARENT_REFLECTION.read_text())
    parent_guard = json.loads(PARENT_GUARD.read_text())
    opened = json.loads(OPEN_DECISION.read_text())
    open_guard = json.loads(OPEN_GUARD.read_text())
    if not (
        parent["promotionPass"] is True
        and parent["measurements"]["gateAdjointMismatchCount"] == 114
        and parent["measurements"]["valueAdjointMismatchCount"] == 0
        and parent["measurements"]["sourceCaptureDeterministic"] is True
        and parent_reflection["validity"]["valid"] is True
        and parent_reflection["hypothesis"]["verdict"] == "supported"
        and parent_reflection["decision"]["verdict"] == "mutate"
        and parent_guard["returncode"] == 0
        and parent_guard["rss_guard_exceeded"] is False
        and parent_guard["temporary_disk_guard_exceeded"] is False
        and opened["measurements"]["sourceFf2InputResidualMismatchCount"] == 0
        and opened["measurements"]["openBackwardDeterministic"] is True
        and open_guard["returncode"] == 0
        and open_guard["rss_guard_exceeded"] is False
        and open_guard["temporary_disk_guard_exceeded"] is False
    ):
        raise ValueError("AVX2 GEGLU gate antecedents are not satisfied")
    library_bound = sha256(LIBNC) == EXPECTED_LIBNC_SHA256
    library = LIBNC.read_bytes()
    kernel_bound = (
        hashlib.sha256(library[KERNEL_START:KERNEL_END]).hexdigest()
        == EXPECTED_KERNEL_SHA256
    )
    return library_bound, kernel_bound


def compile_evaluator() -> tuple[Path, dict[str, Any]]:
    evaluator = WORK / "geglu_gate_avx2"
    receipt = execute(
        [
            os.environ.get("CXX", "g++"),
            "-std=c++17",
            "-O3",
            "-mavx2",
            "-mfma",
            "-ffp-contract=off",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(EVALUATOR_SOURCE),
            "-o",
            str(evaluator),
        ],
        ROOT,
    )
    return evaluator, {"command": receipt, "evaluatorSha256": sha256(evaluator)}


def evaluate(evaluator: Path, label: str) -> dict[str, Any]:
    gate = WORK / f"{label}-gate-adjoint.bf16"
    value = WORK / f"{label}-value-adjoint.bf16"
    receipt = execute(
        [
            str(evaluator),
            str(SOURCE_GATE_INPUT),
            str(SOURCE_VALUE_INPUT),
            str(OPEN_FF2_RESIDUAL),
            str(gate),
            str(value),
        ],
        WORK,
    )
    for path in (gate, value):
        if not path.is_file() or path.stat().st_size != ELEMENTS * 2:
            raise ValueError("AVX2 GEGLU output geometry differs")
    return {
        "receipt": receipt,
        "gatePath": gate,
        "gateSha256": sha256(gate),
        "valuePath": value,
        "valueSha256": sha256(value),
    }


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
        raise ValueError("AVX2 GEGLU source closure exceeds ceiling")


def evaluate_predicates(
    predicates: list[dict[str, Any]], measurements: dict[str, Any]
) -> list[dict[str, Any]]:
    operators = {
        "eq": lambda observed, threshold: observed == threshold,
        "gt": lambda observed, threshold: observed > threshold,
        "lte": lambda observed, threshold: observed <= threshold,
    }
    result = []
    for predicate in predicates:
        observed = measurements[predicate["measurement"]]
        row = dict(predicate)
        row["observed"] = observed
        row["passed"] = operators[predicate["operator"]](
            observed, predicate["threshold"]
        )
        result.append(row)
    return result


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
    expected_experiment = reference(experiment_path)
    expected_experiment.pop("id")
    if expected_experiment != json.loads(
        os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]
    ):
        raise ValueError("job and AVX2 GEGLU experiment bindings differ")
    candidate_revision = json.loads(
        os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"]
    )
    if candidate_revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    library_bound, kernel_bound = require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("AVX2 GEGLU result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("AVX2 GEGLU work root is not fresh")

    baseline_gate = WORK / "retained-gate-adjoint.bf16"
    baseline_value = WORK / "retained-value-adjoint.bf16"
    split_open_residual(OPEN_FF1_RESIDUAL, baseline_gate, baseline_value)
    evaluator, build = compile_evaluator()
    evaluations = [evaluate(evaluator, label) for label in ("a", "b")]
    replay_identical = all(
        evaluations[0][key] == evaluations[1][key]
        for key in ("gateSha256", "valueSha256")
    )
    baseline_source = compare_bf16(baseline_gate, SOURCE_GATE_ADJOINT)
    treatment_source = compare_bf16(
        evaluations[0]["gatePath"], SOURCE_GATE_ADJOINT
    )
    treatment_baseline = compare_bf16(
        evaluations[0]["gatePath"], baseline_gate
    )
    value_source = compare_bf16(
        evaluations[0]["valuePath"], SOURCE_VALUE_ADJOINT
    )
    treatment_artifact = RESULT / "avx2-geglu-gate-adjoint.bf16"
    value_artifact = RESULT / "value-branch-control.bf16"
    shutil.copyfile(evaluations[0]["gatePath"], treatment_artifact)
    shutil.copyfile(evaluations[0]["valuePath"], value_artifact)
    incremental_source = RESULT / "incremental_source.tar.xz"
    source_package(incremental_source)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "build": build,
                "sourceKernelAttribution": {
                    "librarySha256": EXPECTED_LIBNC_SHA256,
                    "kernelOffsetStart": hex(KERNEL_START),
                    "kernelOffsetEndExclusive": hex(KERNEL_END),
                    "kernelSha256": EXPECTED_KERNEL_SHA256,
                    "vectorWidth": 8,
                    "contract": (
                        "bounded exp polynomial -> tanh -> analytic GELU "
                        "derivative -> incoming-adjoint multiply"
                    ),
                },
                "evaluations": [
                    {
                        key: value
                        for key, value in evaluation.items()
                        if not key.endswith("Path")
                    }
                    for evaluation in evaluations
                ],
                "evaluationReplayIdentical": replay_identical,
                "retainedGateSourceComparison": baseline_source,
                "treatmentSourceComparison": treatment_source,
                "treatmentBaselineComparison": treatment_baseline,
                "valueControlSourceComparison": value_source,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    shutil.rmtree(WORK)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "evaluationReplayIdentical": replay_identical,
        "adjointElementCount": treatment_artifact.stat().st_size // 2,
        "retainedGateMismatchCount": baseline_source["mismatchCount"],
        "maximumRetainedGateAbsoluteError": baseline_source[
            "maximumAbsoluteError"
        ],
        "avx2GateMismatchCount": treatment_source["mismatchCount"],
        "maximumAvx2GateAbsoluteError": treatment_source[
            "maximumAbsoluteError"
        ],
        "treatmentChangesBaseline": treatment_baseline["mismatchCount"] > 0,
        "valueControlMismatchCount": value_source["mismatchCount"],
        "maximumValueControlAbsoluteError": value_source[
            "maximumAbsoluteError"
        ],
        "sourceLibraryDigestBound": library_bound,
        "kernelBytesDigestBound": kernel_bound,
        "incrementalSourceBytes": incremental_source.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    promotion = evaluate_predicates(
        experiment["promotionPredicates"], measurements
    )
    kill = evaluate_predicates(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": research_contracts.objective_binding(),
        "experiment": expected_experiment,
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
            reference(execution_path, "execution"),
            reference(treatment_artifact, "avx2-geglu-gate-adjoint"),
            reference(value_artifact, "value-branch-control"),
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
