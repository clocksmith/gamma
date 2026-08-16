#!/usr/bin/env python3
"""Freeze the full-config ABI LibNC gradient-merge retry."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_open_top_pre_ff_rmsnorm_backward_64_q0_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_bf16_gradient_merge_64_q0_retry_v3"
PARENT_ID = "nncp_libnc_bf16_gradient_merge_64_q0_retry_v2"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
PARENT_EXPERIMENT = ROOT / (
    "operations/adaptive/experiments/"
    "nncp_libnc_bf16_gradient_merge_64_q0_retry_v2.json"
)
PARENT_FAILED_JOB = ROOT / (
    "operations/adaptive/failed/000_20260816T145928Z_74068bcb9c.json"
)
PARENT_GUARD = ROOT / "results" / PARENT_ID / "guard.json"
PARENT_LOG = ROOT / "run_logs/adaptive/20260816T145928Z_74068bcb9c.log"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T145928Z_74068bcb9c.json"
)
PROGRAM = ROOT / "programs" / CANDIDATE_ID
DESCRIPTOR = PROGRAM / "program.py"
RUNNER = ROOT / "tools/nncp_libnc_bf16_gradient_merge_64_q0_retry_v3.py"
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
        "Keep the rank-2 evaluator, values, graph orders, controls, "
        "comparators, and digest-bound libnc.so unchanged; compile libnc.h "
        "with the production LIBNC_CONFIG_FULL ABI definition."
    )
    experiment["invariants"].append(
        "The rank-2 parent aborted before its first gradient because its client-side conditional NC type configuration differed from the full-config library."
    )
    inputs = list(experiment["inputs"])
    additions = (
        ("failed-abi-job", PARENT_FAILED_JOB),
        ("failed-abi-guard", PARENT_GUARD),
        ("failed-abi-log", PARENT_LOG),
        ("failed-abi-reflection", PARENT_REFLECTION),
        ("full-config-retry-runner", RUNNER),
        ("full-config-retry-materializer", MATERIALIZER),
        ("full-config-program-descriptor", DESCRIPTOR),
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
