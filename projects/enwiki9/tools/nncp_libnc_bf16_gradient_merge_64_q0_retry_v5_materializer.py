#!/usr/bin/env python3
"""Freeze the F32-injected LibNC gradient-merge retry."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_open_top_pre_ff_rmsnorm_backward_64_q0_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_bf16_gradient_merge_64_q0_retry_v5"
PARENT_ID = "nncp_libnc_bf16_gradient_merge_64_q0_retry_v4"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
PARENT_EXPERIMENT = ROOT / (
    "operations/adaptive/experiments/"
    "nncp_libnc_bf16_gradient_merge_64_q0_retry_v4.json"
)
PARENT_FAILED_JOB = ROOT / (
    "operations/adaptive/failed/000_20260816T150925Z_9e580bcc8b.json"
)
PARENT_GUARD = ROOT / "results" / PARENT_ID / "guard.json"
PARENT_LOG = ROOT / "run_logs/adaptive/20260816T150925Z_9e580bcc8b.log"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T150925Z_9e580bcc8b.json"
)
PROGRAM = ROOT / "programs" / CANDIDATE_ID
EVALUATOR = PROGRAM / "gradient_merge_f32_injection.c"
DESCRIPTOR = PROGRAM / "program.py"
RUNNER = ROOT / "tools/nncp_libnc_bf16_gradient_merge_64_q0_retry_v5.py"
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
        "Keep the shared BF16 parameter, exact coefficient words, graph "
        "orders, controls, comparators, full-config ABI, and library digest; "
        "convert each duplicate parameter path to F32, multiply by an exact "
        "F32 expansion of its BF16 adjoint, reduce, and observe the BF16 "
        "parameter-gradient merge."
    )
    experiment["invariants"].append(
        "Each single path must return its entire original BF16 adjoint exactly, proving that F32 coefficient injection and backward conversion preserve the controlled population before merge interpretation."
    )
    inputs = [
        item for item in experiment["inputs"]
        if item.get("id") != "evaluator-source"
    ]
    additions = (
        ("evaluator-source", EVALUATOR),
        ("failed-matmul-job", PARENT_FAILED_JOB),
        ("failed-matmul-guard", PARENT_GUARD),
        ("failed-matmul-log", PARENT_LOG),
        ("failed-matmul-reflection", PARENT_REFLECTION),
        ("f32-injection-runner", RUNNER),
        ("f32-injection-materializer", MATERIALIZER),
        ("f32-injection-program-descriptor", DESCRIPTOR),
    )
    closure = local_source_closure((RUNNER, MATERIALIZER))
    closure_by_path = {
        path.relative_to(ROOT).as_posix(): path for path in closure
    }
    inputs = [
        base.reference(closure_by_path[item["path"]], item["id"])
        if item["path"] in closure_by_path else item
        for item in inputs
    ]
    present = {item["path"] for item in inputs}
    for identifier, path in additions:
        reference = base.reference(path, identifier)
        if reference["path"] not in present:
            inputs.append(reference)
            present.add(reference["path"])
    for path in closure:
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
