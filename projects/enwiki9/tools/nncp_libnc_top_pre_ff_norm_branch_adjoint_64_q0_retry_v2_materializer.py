#!/usr/bin/env python3
"""Freeze receipt-only finalization of the sealed branch oracle."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_open_top_pre_ff_rmsnorm_backward_64_q0_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v2"
PARENT_ID = "nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / (
    "tools/nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v2.py"
)
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
DESCRIPTOR = PROGRAM / "program.py"
PARENT_EXPERIMENT = ROOT / "operations/adaptive/experiments" / f"{PARENT_ID}.json"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_JOB = ROOT / "operations/adaptive/failed/000_20260816T141750Z_04014220dc.json"
PARENT_LOG = ROOT / "run_logs/adaptive/20260816T141750Z_04014220dc.log"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T141735480097Z_05688e9742bd.json"
)
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T141750Z_04014220dc.json"
)
SOURCE_CEILING = 2_000_000


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    parent = json.loads(PARENT_EXPERIMENT.read_text())
    inputs = [
        base.reference(PARENT_RESULT / "decision.json", "parent-decision"),
        base.reference(PARENT_RESULT / "execution.json", "parent-execution"),
        base.reference(PARENT_RESULT / "guard.json", "parent-guard"),
        base.reference(PARENT_JOB, "parent-job"),
        base.reference(PARENT_LOG, "parent-log"),
        base.reference(PARENT_REVISION, "parent-revision"),
        base.reference(PARENT_REFLECTION, "parent-reflection"),
        base.reference(
            PARENT_RESULT / "source-pre-ff-norm-input.bf16",
            "sealed-normalization-input",
        ),
        base.reference(
            PARENT_RESULT / "source-pre-ff-norm-branch-adjoint.bf16",
            "sealed-normalization-branch-adjoint",
        ),
        base.reference(RUNNER, "runner"),
        base.reference(MATERIALIZER, "materializer"),
        base.reference(DESCRIPTOR, "program-descriptor"),
    ]
    present_paths = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present_paths:
            inputs.append(base.reference(path, base.source_identifier(path)))
            present_paths.add(relative)
    experiment = {
        **parent,
        "experimentId": CANDIDATE_ID,
        "proposalId": CANDIDATE_ID,
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "parent": {
            "candidateId": PARENT_ID,
            "revision": {
                key: value
                for key, value in base.reference(
                    PARENT_REVISION, "parent-revision"
                ).items()
                if key != "id"
            },
        },
        "hypothesis": {
            "claim": (
                "The sealed artifacts and completed measurements can be "
                "finalized by correcting only the result experiment-reference "
                "shape, with zero teacher or arithmetic execution."
            ),
            "falsification": (
                "Any parent-artifact drift, measurement disagreement, copied-"
                "artifact drift, nonzero teacher or arithmetic execution, "
                "predicate failure, schema failure, or resource failure "
                "rejects finalization."
            ),
        },
        "changedMechanism": (
            "Copy the digest-bound sealed tensors, reuse the completed parent "
            "measurements verbatim, construct the experiment reference with "
            "only path and sha256, and validate the strict result schema."
        ),
        "invariants": [
            "The failed seal job, guard, log, revision, reflection, execution, draft decision, and both sealed tensor digests remain bound.",
            "No capture directory is reconstructed and no teacher or normalization arithmetic is executed.",
            "Every scientific measurement is reused from the sealed parent decision without alteration.",
            "Only source-package size and receipt work-root cleanup are recomputed as bookkeeping.",
            "The finalized artifacts retain zero objective credit and cannot ship as teacher evidence.",
        ],
        "controls": [
            {
                "id": "sealed-artifacts",
                "role": "treatment",
                "definition": "Copy both digest-bound tensors from the completed seal without modification.",
            },
            {
                "id": "verbatim-measurements",
                "role": "replay",
                "definition": "Reuse every completed scientific measurement and reevaluate the frozen predicates.",
            },
            {
                "id": "bare-experiment-reference",
                "role": "comparator",
                "definition": "Remove only the forbidden id property from the result experiment reference.",
            },
            {
                "id": "zero-execution-finalizer",
                "role": "negative",
                "definition": "Record zero teacher and zero arithmetic executions in the finalizer execution receipt.",
            },
        ],
        "causalBoundary": {
            "availableInformation": [
                "The sealed parent artifacts, completed measurements, execution manifest, failure receipts, and strict result schema."
            ],
            "forbiddenInformation": [
                "Capture reconstruction, teacher execution, arithmetic recomputation, artifact modification, tolerance, fitted values, or objective credit."
            ],
        },
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/source-pre-ff-norm-input.bf16",
            f"results/{CANDIDATE_ID}/source-pre-ff-norm-branch-adjoint.bf16",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
        ],
    }
    experiment["budget"] = {
        "expectedGrossSavingsBytes": 0,
        "maximumAddedPackageBytes": SOURCE_CEILING,
        "expectedNetSavingsBytes": -SOURCE_CEILING,
    }
    experiment["search"] = {
        "expectedTransferRetention": 1.0,
        "expectedRuntimeRatio": 0.001,
        "expectedMemoryRatio": 0.001,
        "uncertaintyRisk": 0.0,
        "interactionRisk": 0.0,
    }
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
