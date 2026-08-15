#!/usr/bin/env python3
"""Run direct-F32 named-gradient localization against the q2 control."""

from __future__ import annotations

import hashlib
import json
import lzma
import os
from pathlib import Path
import subprocess
import tarfile
import time
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_delta_midas_named_midpoint_gradient as q0
import nncp_libnc_output_head_midpoint_attribution_65536_qm1 as production_q1
import research_contracts
from materialize_nncp_named_midpoint_gradient_q3 import materialize


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "delta_midas_named_midpoint_gradient_65536_q3_v1"
MATERIALIZER = ROOT / "tools/materialize_nncp_named_midpoint_gradient_q3.py"
MIDPOINT_PATCH = production_q1.PROGRAM / "nncp_midsegment32.patch"
Q2_RESULT = ROOT / "results/delta_midas_named_midpoint_gradient_65536_q2_v1/decision.json"
Q2_DETAIL = ROOT / "results/delta_midas_named_midpoint_gradient_65536_q2_v1/gradient-detail.json"
Q2_REFLECTION = ROOT / "operations/adaptive/reflections/20260815T172824Z_465e6837f4.json"
_BASE_SUMMARIZE = q0.summarize
_BASE_EVALUATE = q0.evaluate
_DIRECT_F32_SUMMARY: dict[str, Any] | None = None


def execute(
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    log: Path,
) -> dict[str, Any]:
    started = time.monotonic()
    with log.open("wb") as error_stream:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=error_stream,
            check=False,
        )
    if completed.returncode != 0:
        raise subprocess.CalledProcessError(
            completed.returncode,
            command,
            output=completed.stdout,
            stderr=log.read_bytes(),
        )
    return {
        "command": command,
        "elapsedSeconds": time.monotonic() - started,
        "returncode": completed.returncode,
        "stdoutSha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr": q0.reference(log),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    global _DIRECT_F32_SUMMARY
    _DIRECT_F32_SUMMARY = _BASE_SUMMARIZE(rows)
    return _DIRECT_F32_SUMMARY


def require_q2_lineage() -> None:
    experiment_reference = json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"])
    experiment_path = ROOT / experiment_reference["path"]
    experiment = json.loads(experiment_path.read_text())
    inputs = {item["id"]: item for item in experiment["inputs"]}
    for identifier, path in (
        ("q2-decision", Q2_RESULT),
        ("q2-gradient-detail", Q2_DETAIL),
        ("q2-reflection", Q2_REFLECTION),
    ):
        if inputs.get(identifier) != q0.reference(path, identifier):
            raise ValueError(f"q3 experiment does not bind its {identifier} input")

    research_contracts.validate_artifact(Q2_REFLECTION)
    reflection = json.loads(Q2_REFLECTION.read_text())
    if reflection["candidateId"] != "delta_midas_named_midpoint_gradient_65536_q2_v1":
        raise ValueError("q2 reflection identifies another candidate")
    if reflection["decision"]["verdict"] != "retry":
        raise ValueError("q2 reflection does not authorize an implementation retry")
    if reflection["validity"]["classification"] != "incomplete-evidence":
        raise ValueError("q2 reflection does not preserve the numeric-validity boundary")
    if q0.reference(Q2_RESULT) not in reflection["evidence"]:
        raise ValueError("q2 reflection does not classify the bound q2 result")


def require_fresh_outputs() -> None:
    experiment_reference = json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"])
    experiment = json.loads((ROOT / experiment_reference["path"]).read_text())
    result_root = (ROOT / "results" / CANDIDATE_ID).resolve()
    for output in experiment["outputs"]:
        path = (ROOT / output).resolve()
        if path.parent != result_root:
            raise ValueError(f"q3 output escapes its result boundary: {output}")
        if path.exists():
            raise FileExistsError(f"refusing to reuse q3 output: {path}")


def q2_summary() -> dict[str, Any]:
    require_q2_lineage()
    research_contracts.validate_artifact(Q2_RESULT)
    result = json.loads(Q2_RESULT.read_text())
    if result["candidateId"] != "delta_midas_named_midpoint_gradient_65536_q2_v1":
        raise ValueError("q2 result identifies another candidate")
    artifacts = {item["id"]: item for item in result["artifacts"]}
    if artifacts.get("gradient-detail") != q0.reference(Q2_DETAIL, "gradient-detail"):
        raise ValueError("q2 result does not bind its gradient detail")
    detail = json.loads(Q2_DETAIL.read_text())
    summary = detail.get("summary")
    if not isinstance(summary, dict):
        raise ValueError("q2 gradient detail has no summary")
    return summary


def evaluate(
    predicates: list[dict[str, Any]],
    measurements: dict[str, Any],
) -> list[dict[str, Any]]:
    if "lowPrecisionDominantGroupMatched" not in measurements:
        if _DIRECT_F32_SUMMARY is None:
            raise ValueError("direct F32 summary was not captured")
        low_precision = q2_summary()
        measurements["lowPrecisionDominantGroupMatched"] = (
            low_precision["dominantNonHeadGroup"]
            == _DIRECT_F32_SUMMARY["dominantNonHeadGroup"]
        )
        measurements["lowPrecisionThirdDominantGroupsMatched"] = (
            low_precision["thirdDominantNonHeadGroups"]
            == _DIRECT_F32_SUMMARY["thirdDominantNonHeadGroups"]
        )
        measurements["lowPrecisionMinimumThirdShareAbsoluteDelta"] = abs(
            low_precision["minimumThirdDominantNonHeadShare"]
            - _DIRECT_F32_SUMMARY["minimumThirdDominantNonHeadShare"]
        )
        measurements["lowPrecisionHeadShareAbsoluteDelta"] = abs(
            low_precision["headGroupShare"]
            - _DIRECT_F32_SUMMARY["headGroupShare"]
        )
    return _BASE_EVALUATE(predicates, measurements)


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((Path(__file__), MATERIALIZER)),
        MIDPOINT_PATCH,
    ]
    experiment_reference = json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"])
    experiment = json.loads((ROOT / experiment_reference["path"]).read_text())
    inputs = {item["path"]: item for item in experiment["inputs"]}
    for member in members:
        relative = member.relative_to(ROOT).as_posix()
        expected = inputs.get(relative)
        observed = q0.reference(member)
        if expected is None or any(
            expected.get(key) != observed[key] for key in ("path", "sha256")
        ):
            raise ValueError(f"packaged source drifted from q3 input: {relative}")
    tar_path = path.with_suffix("")
    if tar_path.exists():
        raise FileExistsError(f"refusing to reuse q3 package staging path: {tar_path}")
    with tarfile.open(tar_path, "w") as archive:
        for member in members:
            info = archive.gettarinfo(
                str(member), arcname=member.relative_to(ROOT).as_posix()
            )
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.mtime = 0
            info.mode = 0o644
            with member.open("rb") as stream:
                archive.addfile(info, stream)
    path.write_bytes(
        lzma.compress(tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME)
    )
    tar_path.unlink()


def main() -> int:
    require_q2_lineage()
    require_fresh_outputs()
    q0.CANDIDATE_ID = CANDIDATE_ID
    q0.MATERIALIZER = MATERIALIZER
    q0.materialize = materialize
    q0.execute = execute
    q0.summarize = summarize
    q0.evaluate = evaluate
    q0.source_package = source_package
    return q0.main()


if __name__ == "__main__":
    raise SystemExit(main())
