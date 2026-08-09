#!/usr/bin/env python3
"""Repeat q2 independently and require byte-identical build artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import cmix_obias_source_1m_roundtrip_qm2 as parent


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_source_1m_roundtrip_qm3_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
REFERENCE = ROOT / "results" / "cmix_obias_source_1m_roundtrip_qm2_v1"
ARTIFACTS = ("cmix", "head.blob", "out.cmix", "archive9")


def artifact(path: Path) -> dict[str, object]:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(8 << 20):
            digest.update(chunk)
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": digest.hexdigest(),
    }


def main() -> int:
    for name in ARTIFACTS:
        if not (REFERENCE / name).is_file():
            raise FileNotFoundError(f"missing q2 reference artifact: {name}")

    parent.CANDIDATE_ID = CANDIDATE_ID
    parent.RESULT = RESULT
    returncode = parent.main()
    if returncode != 0:
        return returncode

    comparisons: dict[str, object] = {}
    all_identical = True
    for name in ARTIFACTS:
        reference = artifact(REFERENCE / name)
        reproduced = artifact(RESULT / name)
        identical = (
            reference["bytes"] == reproduced["bytes"]
            and reference["sha256"] == reproduced["sha256"]
        )
        all_identical = all_identical and identical
        comparisons[name] = {
            "reference": reference,
            "reproduced": reproduced,
            "byte_identical": identical,
        }

    decision_path = RESULT / "decision.json"
    decision = json.loads(decision_path.read_text())
    decision["schema"] = "enwiki9_cmix_obias_source_1m_roundtrip_qm3_v1"
    decision["independent_clean_build_identity"] = {
        "reference_candidate_id": "cmix_obias_source_1m_roundtrip_qm2_v1",
        "fresh_source_export": True,
        "fresh_build_scratch": True,
        "artifacts": comparisons,
        "all_artifacts_byte_identical": all_identical,
    }
    if not all_identical:
        decision["status"] = "REJECTED_INDEPENDENT_BUILD_IDENTITY"
        decision["verdict"] = "do_not_authorize_source_built_full_corpus_encode"
        decision["decision"]["promotion_authorized"] = False

    temporary = decision_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    temporary.replace(decision_path)
    print(
        json.dumps(
            {
                "event": "independent_clean_build_identity",
                "all_artifacts_byte_identical": all_identical,
            }
        ),
        flush=True,
    )
    return 0 if all_identical else 1


if __name__ == "__main__":
    raise SystemExit(main())
