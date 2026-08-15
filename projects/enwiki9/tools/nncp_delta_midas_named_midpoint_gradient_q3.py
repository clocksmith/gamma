#!/usr/bin/env python3
"""Run direct-F32 named-gradient localization against the q2 control."""

from __future__ import annotations

import json
import lzma
from pathlib import Path
import tarfile
from typing import Any

import nncp_delta_midas_named_midpoint_gradient as q0
import nncp_delta_midas_named_midpoint_gradient_q1 as q1
import nncp_delta_midas_named_midpoint_gradient_q2 as q2
import nncp_libnc_output_head_midpoint_attribution_65536_qm0 as production_q0
import nncp_libnc_output_head_midpoint_attribution_65536_qm1 as production_q1
import research_contracts
from materialize_nncp_named_midpoint_gradient_q3 import materialize


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "delta_midas_named_midpoint_gradient_65536_q3_v1"
MATERIALIZER = ROOT / "tools/materialize_nncp_named_midpoint_gradient_q3.py"
Q2_MATERIALIZER = ROOT / "tools/materialize_nncp_named_midpoint_gradient_q2.py"
Q1_MATERIALIZER = ROOT / "tools/materialize_nncp_named_midpoint_gradient_q1.py"
Q0_MATERIALIZER = ROOT / "tools/materialize_nncp_named_midpoint_gradient.py"
Q2_RESULT = ROOT / "results/delta_midas_named_midpoint_gradient_65536_q2_v1/decision.json"
Q2_DETAIL = ROOT / "results/delta_midas_named_midpoint_gradient_65536_q2_v1/gradient-detail.json"
_BASE_SUMMARIZE = q0.summarize
_BASE_EVALUATE = q0.evaluate
_DIRECT_F32_SUMMARY: dict[str, Any] | None = None


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    global _DIRECT_F32_SUMMARY
    _DIRECT_F32_SUMMARY = _BASE_SUMMARIZE(rows)
    return _DIRECT_F32_SUMMARY


def q2_summary() -> dict[str, Any]:
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
        Path(__file__),
        Path(q2.__file__),
        Path(q1.__file__),
        Path(q0.__file__),
        MATERIALIZER,
        Q2_MATERIALIZER,
        Q1_MATERIALIZER,
        Q0_MATERIALIZER,
        production_q0.MATERIALIZER,
        Path(production_q0.__file__),
        Path(production_q1.__file__),
    ]
    tar_path = path.with_suffix("")
    with tarfile.open(tar_path, "w") as archive:
        for member in members:
            archive.add(member, arcname=member.relative_to(ROOT))
    path.write_bytes(
        lzma.compress(tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME)
    )
    tar_path.unlink()


def main() -> int:
    q0.CANDIDATE_ID = CANDIDATE_ID
    q0.MATERIALIZER = MATERIALIZER
    q0.materialize = materialize
    q0.execute = q1.execute
    q0.summarize = summarize
    q0.evaluate = evaluate
    q0.source_package = source_package
    return q0.main()


if __name__ == "__main__":
    raise SystemExit(main())
