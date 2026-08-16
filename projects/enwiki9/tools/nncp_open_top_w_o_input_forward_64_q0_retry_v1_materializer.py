#!/usr/bin/env python3
"""Freeze the fixture-root repair retry for the open pre-w_o forward."""

from __future__ import annotations

import copy
import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_open_top_w_o_input_forward_64_q0_materializer as parent
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_w_o_input_forward_64_q0_retry_v1"
PARENT_ID = "nncp_open_top_w_o_input_forward_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RUNNER = ROOT / "tools/nncp_open_top_w_o_input_forward_64_q0_retry_v1.py"
MATERIALIZER = Path(__file__).resolve()
DESCRIPTOR = PROGRAM / "program.py"
CMAKE = PROGRAM / "CMakeLists.txt"
FORWARD_MATERIALIZER = PROGRAM / "materialize_forward.py"
FAILED_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T165333Z_93ccd444ea.json"
)
FAILED_GUARD = ROOT / (
    "results/nncp_open_top_w_o_input_forward_64_q0_v1/guard.json"
)
PARENT_EXPERIMENT = ROOT / (
    "operations/adaptive/experiments/nncp_open_top_w_o_input_forward_64_q0_v1.json"
)
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    experiment = copy.deepcopy(json.loads(PARENT_EXPERIMENT.read_text()))
    experiment["experimentId"] = CANDIDATE_ID
    experiment["proposalId"] = CANDIDATE_ID
    experiment["parent"] = {
        "candidateId": PARENT_ID,
        "revision": {
            key: value
            for key, value in parent.reference(
                ROOT
                / json.loads(FAILED_REFLECTION.read_text())["candidateRevision"][
                    "receipt"
                ]["path"],
                "parent-revision",
            ).items()
            if key != "id"
        },
    }
    experiment["changedMechanism"] = (
        "Preserve the prospectively frozen forward exposure, arithmetic, "
        "population, controls, and predicates while creating the runner-owned "
        "fixtures parent before leaf materialization."
    )
    experiment["invariants"].append(
        "The retry changes only fixture-directory setup; scientific treatment, comparator, and arithmetic remain identical."
    )
    experiment["causalBoundary"]["availableInformation"].append(
        "The failed attempt reflection localized a pre-science missing-parent directory error."
    )
    excluded = {
        "forward-materializer",
        "cmake",
        "runner",
        "materializer",
        "program-descriptor",
    }
    inputs = [
        item
        for item in experiment["inputs"]
        if item["id"] not in excluded
        and not item["id"].startswith("runtime-source-")
    ]
    inputs.extend(
        (
            parent.reference(FAILED_REFLECTION, "failed-attempt-reflection"),
            parent.reference(FAILED_GUARD, "failed-attempt-guard"),
            parent.reference(FORWARD_MATERIALIZER, "forward-materializer"),
            parent.reference(CMAKE, "cmake"),
            parent.reference(RUNNER, "runner"),
            parent.reference(MATERIALIZER, "materializer"),
            parent.reference(DESCRIPTOR, "program-descriptor"),
        )
    )
    present = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present:
            inputs.append(parent.reference(path, parent.source_identifier(path)))
            present.add(relative)
    experiment["inputs"] = inputs
    experiment["outputs"] = [
        f"results/{CANDIDATE_ID}/decision.json",
        f"results/{CANDIDATE_ID}/execution.json",
        f"results/{CANDIDATE_ID}/open-exact-w-o-input.bf16",
        f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
    ]
    experiment["generatedUtc"] = (
        dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    )
    OUTPUT.write_text(json.dumps(experiment, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(OUTPUT)
    print(OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
