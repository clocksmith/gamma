#!/usr/bin/env python3
"""Run the open top-FF2 tail with the source-exact streaming RMSNorm dot."""

from __future__ import annotations

import json
import lzma
from pathlib import Path
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_open_profile_top_ff2_gradient_64_q0_retry_v1 as implementation


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_v1"
PARENT_ID = "nncp_open_profile_top_ff2_gradient_64_q0_retry_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
PARENT_DECISION = ROOT / "results" / PARENT_ID / "decision.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T061837Z_1dfa2ae8f8.json"
)
PARENT_RESIDUAL = ROOT / "results" / PARENT_ID / "open-final-hidden-residual.bf16"
DOT_ID = "nncp_libnc_final_rmsnorm_reduction_scale_64_q0_v1"
DOT_RESULT = ROOT / "results" / DOT_ID
DOT_DECISION = DOT_RESULT / "decision.json"
DOT_EXECUTION = DOT_RESULT / "execution.json"
DOT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T075342Z_b33521b4a0.json"
)
SOURCE_EXACT_ADJOINT = DOT_RESULT / "source-exact-final-rms-adjoint.bf16"
RUNNER = Path(__file__).resolve()
FREEZER = ROOT / (
    "tools/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_v1_materializer.py"
)


implementation.CANDIDATE_ID = CANDIDATE_ID
implementation.PARENT_ID = PARENT_ID
implementation.PROGRAM = PROGRAM
implementation.RESULT = RESULT
implementation.WORK = RESULT / "work"
implementation.PARENT_DECISION = PARENT_DECISION
implementation.PARENT_REFLECTION = PARENT_REFLECTION
implementation.PARENT_RESIDUAL = PARENT_RESIDUAL
implementation.MATERIALIZER = PROGRAM / "materialize_forward.py"
implementation.CMAKE = PROGRAM / "CMakeLists.txt"
implementation.NORM_REDUCER = PROGRAM / "final_norm_backward.cpp"
implementation.FF2_REDUCER = PROGRAM / "top_ff2_gradient.cpp"
implementation.PROGRAM_DESCRIPTOR = PROGRAM / "program.py"


base_require_inputs = implementation.require_inputs
base_evaluate = implementation.evaluate


def require_inputs(experiment: dict[str, Any]) -> None:
    base_require_inputs(experiment)
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("stream-dot-decision", DOT_DECISION),
        ("stream-dot-execution", DOT_EXECUTION),
        ("stream-dot-reflection", DOT_REFLECTION),
        ("source-exact-final-rms-adjoint", SOURCE_EXACT_ADJOINT),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != implementation.reference(path, identifier):
            raise ValueError(f"stream-dot experiment input drifted: {identifier}")
    decision = json.loads(DOT_DECISION.read_text())
    reflection = json.loads(DOT_REFLECTION.read_text())
    if not (
        decision["measurements"]["streamDotWidthScaledMismatchCount"] == 0
        and decision["measurements"]["baselineSourceMismatchCount"] == 8
        and reflection["validity"]["valid"] is True
        and reflection["attribution"]["causalConfidence"] == "high"
        and reflection["decision"]["verdict"] == "mutate"
    ):
        raise ValueError("stream-dot attribution antecedents are not satisfied")


def evaluate(
    predicates: list[dict[str, Any]],
    measurements: dict[str, bool | int | float],
) -> list[dict[str, Any]]:
    if "sourceFinalNormResidualMismatchCount" not in measurements:
        mismatch_count, maximum_error = implementation.parent.compare_bf16(
            RESULT / "open-final-norm-input-residual.bf16",
            SOURCE_EXACT_ADJOINT,
        )
        measurements["sourceFinalNormResidualMismatchCount"] = mismatch_count
        measurements["maximumSourceFinalNormResidualAbsoluteError"] = (
            maximum_error
        )
    return base_evaluate(predicates, measurements)


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, FREEZER)),
        implementation.MATERIALIZER.resolve(),
        implementation.CMAKE.resolve(),
        implementation.NORM_REDUCER.resolve(),
        implementation.FF2_REDUCER.resolve(),
        implementation.PROGRAM_DESCRIPTOR.resolve(),
        implementation.parent.REDUCER.resolve(),
        implementation.parent.OPEN_SOURCE.resolve(),
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
    compressed = lzma.compress(
        tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME
    )
    tar_path.unlink()
    if len(compressed) > implementation.SOURCE_CEILING:
        raise ValueError("stream-dot open FF2 source closure exceeds ceiling")
    path.write_bytes(compressed)


implementation.require_inputs = require_inputs
implementation.evaluate = evaluate
implementation.source_package = source_package


if __name__ == "__main__":
    raise SystemExit(implementation.main())
