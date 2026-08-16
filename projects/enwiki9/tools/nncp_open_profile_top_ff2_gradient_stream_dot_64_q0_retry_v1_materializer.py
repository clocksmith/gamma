#!/usr/bin/env python3
"""Freeze the immutable retry of the streaming-dot open top-FF2 gate."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_v1_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v1"
FAILED_ID = "nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_v1"
FAILED_EXPERIMENT = ROOT / (
    f"operations/adaptive/experiments/{FAILED_ID}.json"
)
FAILED_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{FAILED_ID}/20260816T075950037050Z_f11016d9628e.json"
)
FAILED_GUARD = ROOT / f"results/{FAILED_ID}/guard.json"
FAILED_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T080014Z_9da1ba0532.json"
)
RUNNER = ROOT / (
    "tools/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v1.py"
)
MATERIALIZER = Path(__file__).resolve()
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    experiment = json.loads(FAILED_EXPERIMENT.read_text())
    experiment["experimentId"] = CANDIDATE_ID
    experiment["proposalId"] = CANDIDATE_ID
    experiment["parent"] = {
        "candidateId": FAILED_ID,
        "revision": {
            "path": FAILED_REVISION.relative_to(ROOT).as_posix(),
            "sha256": f"sha256:{base.sha256(FAILED_REVISION)}",
        },
    }
    replacements = {
        "runner": base.reference(RUNNER, "runner"),
        "materializer": base.reference(MATERIALIZER, "materializer"),
    }
    inputs = [replacements.get(item["id"], item) for item in experiment["inputs"]]
    additions = [
        base.reference(FAILED_GUARD, "failed-preflight-guard"),
        base.reference(FAILED_REFLECTION, "failed-preflight-reflection"),
    ]
    existing_ids = {item["id"] for item in inputs}
    inputs.extend(item for item in additions if item["id"] not in existing_ids)
    present_paths = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present_paths:
            inputs.append(base.reference(path, base.source_identifier(path)))
            present_paths.add(relative)
    experiment["inputs"] = inputs
    experiment["generatedUtc"] = (
        dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    )
    OUTPUT.write_text(json.dumps(experiment, indent=2, sort_keys=True) + "\n")
    try:
        research_contracts.validate_artifact(OUTPUT)
    except Exception:
        OUTPUT.unlink(missing_ok=True)
        raise
    print(OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
