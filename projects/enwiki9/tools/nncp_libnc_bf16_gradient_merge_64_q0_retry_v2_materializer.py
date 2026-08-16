#!/usr/bin/env python3
"""Freeze the production-rank LibNC gradient-merge retry."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_open_top_pre_ff_rmsnorm_backward_64_q0_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_bf16_gradient_merge_64_q0_retry_v2"
PARENT_ID = "nncp_libnc_bf16_gradient_merge_64_q0_retry_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
PARENT_EXPERIMENT = ROOT / (
    "operations/adaptive/experiments/"
    "nncp_libnc_bf16_gradient_merge_64_q0_retry_v1.json"
)
PARENT_FAILED_JOB = ROOT / (
    "operations/adaptive/failed/000_20260816T145446Z_b081961542.json"
)
PARENT_GUARD = ROOT / "results" / PARENT_ID / "guard.json"
PARENT_LOG = ROOT / "run_logs/adaptive/20260816T145446Z_b081961542.log"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T145446Z_b081961542.json"
)
PROGRAM = ROOT / "programs" / CANDIDATE_ID
EVALUATOR = PROGRAM / "gradient_merge_rank2.c"
DESCRIPTOR = PROGRAM / "program.py"
RUNNER = ROOT / "tools/nncp_libnc_bf16_gradient_merge_64_q0_retry_v2.py"
MATERIALIZER = Path(__file__).resolve()


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    parent_job = json.loads(PARENT_FAILED_JOB.read_text())
    experiment = json.loads(PARENT_EXPERIMENT.read_text())
    experiment["experimentId"] = CANDIDATE_ID
    experiment["proposalId"] = CANDIDATE_ID
    experiment["parent"] = {
        "candidateId": PARENT_ID,
        "revision": parent_job["candidate_revision"],
    }
    experiment["changedMechanism"] = (
        "Keep every BF16 word, graph order, control, comparator, and library "
        "digest unchanged; restore the production tensor geometry as 1,024 "
        "features by 2,048 state-stream columns instead of an unsupported "
        "rank-1 flattening."
    )
    experiment["invariants"].append(
        "The rank-1 parent aborted at its first nc_mul before any gradient existed; column-major serialization in this retry remains state-stream-feature order."
    )
    experiment["population"]["coordinate"] = (
        "LibNC rank 2: feature axis 0 and chronological state-stream column axis 1; serialized state-major, stream-major, feature-major"
    )
    inputs = [
        item for item in experiment["inputs"]
        if item.get("id") != "evaluator-source"
    ]
    additions = (
        ("evaluator-source", EVALUATOR),
        ("failed-rank1-job", PARENT_FAILED_JOB),
        ("failed-rank1-guard", PARENT_GUARD),
        ("failed-rank1-log", PARENT_LOG),
        ("failed-rank1-reflection", PARENT_REFLECTION),
        ("rank2-retry-runner", RUNNER),
        ("rank2-retry-materializer", MATERIALIZER),
        ("rank2-program-descriptor", DESCRIPTOR),
    )
    present = {item["path"] for item in inputs}
    for identifier, path in additions:
        reference = base.reference(path, identifier)
        if reference["path"] not in present:
            inputs.append(reference)
            present.add(reference["path"])
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present:
            inputs.append(base.reference(path, base.source_identifier(path)))
            present.add(relative)
    experiment["inputs"] = inputs
    experiment["outputs"] = [
        path.replace(PARENT_ID, CANDIDATE_ID)
        for path in experiment["outputs"]
    ]
    experiment["generatedUtc"] = dt.datetime.now(dt.timezone.utc).replace(
        microsecond=0
    ).isoformat()
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
