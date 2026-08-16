#!/usr/bin/env python3
"""Freeze the corrected same-run contribution attribution oracle."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_open_top_pre_ff_rmsnorm_backward_64_q0_materializer as refs
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v1"
PARENT_ID = "nncp_libnc_pre_ff_same_run_contributions_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
PARENT_EXPERIMENT = ROOT / (
    "operations/adaptive/experiments/"
    "nncp_libnc_pre_ff_same_run_contributions_64_q0_v1.json"
)
PARENT_FAILED_JOB = ROOT / (
    "operations/adaptive/failed/000_20260816T152241Z_ffa4b11ac5.json"
)
PARENT_GUARD = ROOT / "results" / PARENT_ID / "guard.json"
PARENT_LOG = ROOT / "run_logs/adaptive/20260816T152241Z_ffa4b11ac5.log"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T152241Z_ffa4b11ac5.json"
)
RUNNER = ROOT / (
    "tools/nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v1.py"
)
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
        "Preserve the complete source graph, three zero-marker boundaries, "
        "population, controls, composition, predicates, and limits; remove "
        "only the stale assertion that the superseded intermediate branch "
        "comparator had already matched the source."
    )
    experiment["invariants"].append(
        "The corrected antecedent still binds the promoted sealed source branch; only its superseded intermediate mismatch field is no longer treated as an exactness authority."
    )
    inputs = list(experiment["inputs"])
    additions = (
        ("failed-antecedent-job", PARENT_FAILED_JOB),
        ("failed-antecedent-guard", PARENT_GUARD),
        ("failed-antecedent-log", PARENT_LOG),
        ("failed-antecedent-reflection", PARENT_REFLECTION),
        ("corrected-runner", RUNNER),
        ("corrected-materializer", MATERIALIZER),
        ("corrected-program-descriptor", DESCRIPTOR),
    )
    closure = local_source_closure((RUNNER, MATERIALIZER))
    closure_by_path = {
        path.relative_to(ROOT).as_posix(): path for path in closure
    }
    inputs = [
        refs.reference(closure_by_path[item["path"]], item["id"])
        if item["path"] in closure_by_path else item
        for item in inputs
    ]
    present = {item["path"] for item in inputs}
    for identifier, path in additions:
        reference = refs.reference(path, identifier)
        if reference["path"] not in present:
            inputs.append(reference)
            present.add(reference["path"])
    for path in closure:
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present:
            inputs.append(refs.reference(path, refs.source_identifier(path)))
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
