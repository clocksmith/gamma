#!/usr/bin/env python3
"""Freeze the compile-policy-only LibNC gradient-merge retry."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_open_top_pre_ff_rmsnorm_backward_64_q0_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_bf16_gradient_merge_64_q0_retry_v1"
PARENT_ID = "nncp_libnc_bf16_gradient_merge_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
PARENT_EXPERIMENT = ROOT / (
    "operations/adaptive/experiments/"
    "nncp_libnc_bf16_gradient_merge_64_q0_v1.json"
)
PARENT_FAILED_JOB = ROOT / (
    "operations/adaptive/failed/000_20260816T145040Z_23cb743928.json"
)
PARENT_GUARD = ROOT / "results" / PARENT_ID / "guard.json"
PARENT_LOG = ROOT / "run_logs/adaptive/20260816T145040Z_23cb743928.log"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T145040Z_23cb743928.json"
)
RUNNER = ROOT / "tools/nncp_libnc_bf16_gradient_merge_64_q0_retry_v1.py"
MATERIALIZER = Path(__file__).resolve()
DESCRIPTOR = ROOT / "programs" / CANDIDATE_ID / "program.py"


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
        "Keep the evaluator, LibNC digest, data, graph variants, controls, "
        "comparators, and predicates unchanged; suppress only unused-parameter "
        "warnings emitted by immutable external LibNC inline headers while "
        "retaining -Werror for all other diagnostics."
    )
    experiment["invariants"].append(
        "The failed parent stopped at compilation before any graph execution; this retry changes no scientific mechanism or population."
    )
    additions = (
        ("failed-parent-job", PARENT_FAILED_JOB),
        ("failed-parent-guard", PARENT_GUARD),
        ("failed-parent-log", PARENT_LOG),
        ("failed-parent-reflection", PARENT_REFLECTION),
        ("retry-runner", RUNNER),
        ("retry-materializer", MATERIALIZER),
        ("retry-program-descriptor", DESCRIPTOR),
    )
    inputs = list(experiment["inputs"])
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
