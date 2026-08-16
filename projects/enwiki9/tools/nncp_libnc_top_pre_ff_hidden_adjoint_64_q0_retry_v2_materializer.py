#!/usr/bin/env python3
"""Freeze finalization of the sealed top pre-FF source oracle."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2"
PARENT_ID = "nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
DESCRIPTOR = PROGRAM / "program.py"
PARENT_EXPERIMENT = ROOT / (
    "operations/adaptive/experiments/"
    "nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v1.json"
)
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_JOB = ROOT / (
    "operations/adaptive/failed/000_20260816T130215Z_9a50367a99.json"
)
PARENT_LOG = ROOT / "run_logs/adaptive/20260816T130215Z_9a50367a99.log"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    "nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v1/"
    "20260816T130158991978Z_0472db71dab5.json"
)
HIDDEN = PARENT_RESULT / "source-pre-ff-hidden.bf16"
ADJOINT = PARENT_RESULT / "source-pre-ff-hidden-adjoint.bf16"
NORMALIZED_INPUT = ROOT / (
    "results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1/"
    "open-ff1-input.bf16"
)
NORMALIZED_ADJOINT = ROOT / (
    "results/nncp_open_top_ff1_input_adjoint_block128_64_q0_v1/"
    "source-exact-ff1-input-adjoint.bf16"
)
SOURCE_CEILING = 2_000_000
HYPOTHESIS = (
    "The first seal retained both exact source artifacts and two byte-identical "
    "complete capture manifests before misreading a named comparator result as "
    "a tuple; recomputing only the two comparisons yields a valid oracle without "
    "teacher execution."
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path: Path, identifier: str) -> dict[str, str]:
    resolved = path.resolve()
    if ROOT.resolve() not in resolved.parents or not resolved.is_file():
        raise ValueError(f"experiment input is not a project file: {path}")
    return {
        "id": identifier,
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{sha256(resolved)}",
    }


def source_identifier(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    suffix = hashlib.sha256(relative.encode()).hexdigest()[:12]
    return f"runtime-source-{path.stem}-{suffix}"


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    parent = json.loads(PARENT_EXPERIMENT.read_text())
    inputs = [
        reference(PARENT_EXECUTION, "parent-execution"),
        reference(PARENT_GUARD, "parent-guard"),
        reference(PARENT_JOB, "parent-job"),
        reference(PARENT_LOG, "parent-log"),
        reference(PARENT_REVISION, "parent-revision"),
        reference(HIDDEN, "sealed-pre-ff-hidden"),
        reference(ADJOINT, "sealed-pre-ff-hidden-adjoint"),
        reference(NORMALIZED_INPUT, "normalized-ff1-input"),
        reference(NORMALIZED_ADJOINT, "normalized-ff1-input-adjoint"),
        reference(RUNNER, "runner"),
        reference(MATERIALIZER, "materializer"),
        reference(DESCRIPTOR, "program-descriptor"),
    ]
    present = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present:
            inputs.append(reference(path, source_identifier(path)))
            present.add(relative)
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
                "path": PARENT_REVISION.relative_to(ROOT).as_posix(),
                "sha256": f"sha256:{sha256(PARENT_REVISION)}",
            },
        },
        "hypothesis": {
            "claim": HYPOTHESIS,
            "falsification": "Any sealed-artifact drift, manifest disagreement, probe-population failure, non-probe drift, dead boundary control, typed comparison failure, or result-validation failure rejects finalization.",
        },
        "changedMechanism": "Do not execute or reconstruct the teacher. Copy the two sealed artifacts, retain the two identical complete capture-manifest digests and exact fixture-identity rows, and recompute only the two BF16 comparison records through their named fields.",
        "invariants": [
            "The failed seal job, candidate revision, guard, log, execution manifest, and both sealed artifact digests remain bound.",
            "Both complete source capture manifests have one identical aggregate digest.",
            "Both exact probe populations and all non-probe fixture identity rows remain valid.",
            "No teacher, model, optimizer, source graph, or deleted transient capture is executed or reconstructed.",
            "The finalized tensors remain zero-credit oracle evidence and cannot ship in a Gamma codec.",
        ],
        "controls": [
            {"id": "sealed-artifacts", "role": "treatment", "definition": "Copy both digest-bound tensors from the completed first seal without modification."},
            {"id": "twin-manifest-aggregate", "role": "replay", "definition": "Require the two complete original capture manifests to retain one aggregate digest."},
            {"id": "exact-fixture-identity", "role": "comparator", "definition": "Require both exact declared probe populations and zero non-probe drift from the sealed execution."},
            {"id": "typed-boundary-comparisons", "role": "negative", "definition": "Read mismatchCount from the named comparison record and require both boundary controls to remain live."},
        ],
        "causalBoundary": {
            "availableInformation": [
                "The sealed artifacts, complete aggregate manifest digests, exact fixture-identity rows, normalized branch operands, and hash-bound failure receipts."
            ],
            "forbiddenInformation": [
                "Teacher execution, reconstruction of deleted capture scratch, artifact modification, tolerance, coordinate correction, fitted values, or objective credit."
            ],
        },
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/source-pre-ff-hidden.bf16",
            f"results/{CANDIDATE_ID}/source-pre-ff-hidden-adjoint.bf16",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
        ],
    }
    experiment["budget"] = {
        "expectedGrossSavingsBytes": 0,
        "maximumAddedPackageBytes": SOURCE_CEILING,
        "expectedNetSavingsBytes": -SOURCE_CEILING,
    }
    OUTPUT.write_text(json.dumps(experiment, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(OUTPUT)
    print(OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
