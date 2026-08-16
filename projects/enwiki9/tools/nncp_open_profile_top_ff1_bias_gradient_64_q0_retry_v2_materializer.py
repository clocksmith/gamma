#!/usr/bin/env python3
"""Freeze the invocation-corrected exact-FF2 top-FF1 replay."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v1_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v2"
PARENT_ID = "nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v1"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T094656418539Z_8baab96944e4.json"
)
PARENT_EXPERIMENT = ROOT / f"operations/adaptive/experiments/{PARENT_ID}.json"
INVOCATION_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T094657Z_e9fe7b3dcc.json"
)
RUNNER = ROOT / "tools/nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v2.py"
MATERIALIZER = Path(__file__).resolve()
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
contracts = base.contracts


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    experiment = json.loads(PARENT_EXPERIMENT.read_text())
    experiment["experimentId"] = CANDIDATE_ID
    experiment["proposalId"] = CANDIDATE_ID
    experiment["parent"] = {
        "candidateId": PARENT_ID,
        "revision": {
            "path": PARENT_REVISION.relative_to(ROOT).as_posix(),
            "sha256": f"sha256:{contracts.sha256(PARENT_REVISION)}",
        },
    }
    experiment["hypothesis"] = {
        "claim": (
            "With the complete guarded invocation restored and no arithmetic "
            "change, the exact 128-panel FF2 transpose preserves the source "
            "adjoint and the frozen GEGLU backward either exactly reconstructs "
            "or causally fails the retained ff_bias1_19 gradient."
        ),
        "falsification": (
            "Any antecedent, forward, source-adjoint, retained-gradient, replay, "
            "control, dependency, source-size, strict-output, or resource failure "
            "prevents promotion."
        ),
    }
    experiment["changedMechanism"] = (
        "No arithmetic or scientific predicate changes. Bind the terminal "
        "implementation-failure reflection and restore the complete guarded "
        "runner invocation with explicit experiment and output arguments."
    )
    experiment["invariants"].append(
        "The retry candidate is byte-identical to its parent for every arithmetic source file."
    )
    replacements = {
        "runner": contracts.reference(RUNNER, "runner"),
        "materializer": contracts.reference(MATERIALIZER, "materializer"),
    }
    inputs = [replacements.get(item["id"], item) for item in experiment["inputs"]]
    invocation = contracts.reference(
        INVOCATION_REFLECTION, "invocation-failure-reflection"
    )
    inputs = [item for item in inputs if item["id"] != invocation["id"]]
    inputs.append(invocation)
    present_paths = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present_paths:
            inputs.append(
                contracts.reference(path, contracts.source_identifier(path))
            )
            present_paths.add(relative)
    experiment["inputs"] = inputs
    experiment["outputs"] = [
        f"results/{CANDIDATE_ID}/decision.json",
        f"results/{CANDIDATE_ID}/execution.json",
        f"results/{CANDIDATE_ID}/open-ff2-input-residual.bf16",
        f"results/{CANDIDATE_ID}/open-ff1-output-residual.bf16",
        f"results/{CANDIDATE_ID}/open-ff-bias1-19-gradient.bf16",
        f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
    ]
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
