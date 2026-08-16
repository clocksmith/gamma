#!/usr/bin/env python3
"""Retry the open layer-19 pre-w_o forward after fixture-root repair."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import nncp_open_top_w_o_input_forward_64_q0 as base


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_w_o_input_forward_64_q0_retry_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
FAILED_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T165333Z_93ccd444ea.json"
)
FAILED_GUARD = ROOT / (
    "results/nncp_open_top_w_o_input_forward_64_q0_v1/guard.json"
)
MATERIALIZER = ROOT / (
    "tools/nncp_open_top_w_o_input_forward_64_q0_retry_v1_materializer.py"
)


base.CANDIDATE_ID = CANDIDATE_ID
base.PROGRAM = PROGRAM
base.RESULT = RESULT
base.WORK = RESULT / "work"
base.FORWARD_MATERIALIZER = PROGRAM / "materialize_forward.py"
base.CMAKE = PROGRAM / "CMakeLists.txt"
base.PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
base.MATERIALIZER = MATERIALIZER
base.RUNNER = Path(__file__).resolve()

original_require_inputs = base.require_inputs
original_materialize_stream_fixture = base.forward.materialize_stream_fixture


def require_inputs(experiment: dict[str, Any]) -> None:
    original_require_inputs(experiment)
    inputs = {item["id"]: item for item in experiment["inputs"]}
    if inputs.get("failed-attempt-reflection") != base.reference(
        FAILED_REFLECTION, "failed-attempt-reflection"
    ):
        raise ValueError("retry experiment does not bind the failed reflection")
    if inputs.get("failed-attempt-guard") != base.reference(
        FAILED_GUARD, "failed-attempt-guard"
    ):
        raise ValueError("retry experiment does not bind the failed guard")
    reflection = json.loads(FAILED_REFLECTION.read_text())
    guard = json.loads(FAILED_GUARD.read_text())
    if not (
        reflection["validity"]["classification"] == "implementation-failure"
        and reflection["hypothesis"]["verdict"] == "not-tested"
        and reflection["decision"]["verdict"] == "retry"
        and guard["status"] == "complete"
        and guard["returncode"] == 1
        and guard["rss_guard_exceeded"] is False
        and guard["temporary_disk_guard_exceeded"] is False
    ):
        raise ValueError("failed attempt does not authorize the retry")


def materialize_stream_fixture(*args: object, **kwargs: object) -> None:
    fixture = args[4] if len(args) >= 5 else kwargs["fixture"]
    if not isinstance(fixture, Path):
        raise TypeError("fixture path is not a Path")
    fixture.parent.mkdir(parents=True, exist_ok=True)
    original_materialize_stream_fixture(*args, **kwargs)


base.require_inputs = require_inputs
base.forward.materialize_stream_fixture = materialize_stream_fixture


if __name__ == "__main__":
    raise SystemExit(base.main())
