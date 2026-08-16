#!/usr/bin/env python3
"""Freeze the unique-anchor GEGLU branch-capture retry."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_top_geglu_branch_adjoints_64_q0_v1_materializer as parent
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_geglu_branch_adjoints_64_q0_retry_v1"
PARENT_ID = "nncp_libnc_top_geglu_branch_adjoints_64_q0_v1"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T100829363736Z_eb8181e96522.json"
)
PARENT_EXPERIMENT = ROOT / f"operations/adaptive/experiments/{PARENT_ID}.json"
FAILURE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T100841Z_829771fc57.json"
)
RUNNER = ROOT / "tools/nncp_libnc_top_geglu_branch_adjoints_64_q0_retry_v1.py"
MATERIALIZER = Path(__file__).resolve()
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
base = parent.base


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
            "sha256": f"sha256:{base.sha256(PARENT_REVISION)}",
        },
    }
    experiment["hypothesis"] = {
        "claim": (
            "With the source patch bound to the unique FF_ACT_GEGLU case and no "
            "probe or predicate change, at least one production split-branch "
            "adjoint differs from the open branch residual after the incoming "
            "FF2 residual is source-exact."
        ),
        "falsification": (
            "If both complete branch adjoints equal their open counterparts, the "
            "GEGLU backward is exonerated and the mismatch is localized to bias "
            "projection. Any capture, replay, fixture, source, strict-output, or "
            "resource failure invalidates the attribution."
        ),
    }
    experiment["changedMechanism"] = (
        "Change only the source patch anchor from a non-unique nc_split statement "
        "to the complete unique FF_ACT_GEGLU case prefix. Preserve probe placement, "
        "capture payloads, comparisons, predicates, and limits."
    )
    experiment["invariants"].append(
        "The retry changes no probe, calculation, comparison, scientific predicate, or resource ceiling."
    )
    replacements = {
        "runner": base.reference(RUNNER, "runner"),
        "materializer": base.reference(MATERIALIZER, "materializer"),
    }
    inputs = [replacements.get(item["id"], item) for item in experiment["inputs"]]
    failure = base.reference(
        FAILURE_REFLECTION, "source-anchor-failure-reflection"
    )
    inputs = [item for item in inputs if item["id"] != failure["id"]]
    inputs.append(failure)
    present_paths = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present_paths:
            inputs.append(base.reference(path, base.source_identifier(path)))
            present_paths.add(relative)
    experiment["inputs"] = inputs
    experiment["outputs"] = [
        f"results/{CANDIDATE_ID}/decision.json",
        f"results/{CANDIDATE_ID}/execution.json",
        f"results/{CANDIDATE_ID}/source-geglu-gate-input.bf16",
        f"results/{CANDIDATE_ID}/source-geglu-gate-adjoint.bf16",
        f"results/{CANDIDATE_ID}/source-geglu-value-input.bf16",
        f"results/{CANDIDATE_ID}/source-geglu-value-adjoint.bf16",
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
