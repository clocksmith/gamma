#!/usr/bin/env python3
"""Freeze sealing of the completed top pre-FF source captures."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v1"
PARENT_ID = "nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v1.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
DESCRIPTOR = PROGRAM / "program.py"
PARENT_EXPERIMENT = ROOT / (
    "operations/adaptive/experiments/"
    "nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_v1.json"
)
PARENT_GUARD = ROOT / (
    "results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_v1/guard.json"
)
PARENT_JOB = ROOT / (
    "operations/adaptive/failed/000_20260816T124600Z_7c726d2560.json"
)
PARENT_LOG = ROOT / "run_logs/adaptive/20260816T124600Z_7c726d2560.log"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    "nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_v1/"
    "20260816T124540281418Z_85e687c692c5.json"
)
NORMALIZED_INPUT = ROOT / (
    "results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1/"
    "open-ff1-input.bf16"
)
NORMALIZED_ADJOINT = ROOT / (
    "results/nncp_open_top_ff1_input_adjoint_block128_64_q0_v1/"
    "source-exact-ff1-input-adjoint.bf16"
)
FIXTURE_MANIFEST = ROOT / (
    "results/nncp_libnc_profile_update_fixture_64_q3_v1/fixture-manifest.json"
)
SOURCE_CEILING = 2_000_000
HYPOTHESIS = (
    "The failed parent completed two exact source captures before a Python "
    "comparator lookup failed; sealing those immutable directories with the "
    "correct shared comparator preserves the prospective scientific population "
    "without rerunning the teacher."
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
        reference(PARENT_EXPERIMENT, "parent-experiment"),
        reference(PARENT_GUARD, "parent-guard"),
        reference(PARENT_JOB, "parent-job"),
        reference(PARENT_LOG, "parent-log"),
        reference(PARENT_REVISION, "parent-revision"),
        reference(NORMALIZED_INPUT, "normalized-ff1-input"),
        reference(NORMALIZED_ADJOINT, "normalized-ff1-input-adjoint"),
        reference(FIXTURE_MANIFEST, "production-fixture-manifest"),
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
            "falsification": "Any incomplete declared probe population, non-probe fixture drift, replay mismatch, missing failed-job binding, changed resource result, zero comparator, source failure, or sealing-resource failure rejects the retry.",
        },
        "changedMechanism": "Do not rerun the teacher. Read only the two completed capture directories left by the failed parent, invoke the established shared BF16 comparator, seal exact outputs and manifests, then remove the transient 10GB capture tree.",
        "invariants": [
            "The parent experiment, candidate revision, failed job, terminal guard, and exact post-capture AttributeError remain hash-bound.",
            "Each completed directory must contain exactly the declared top_pre_ff_ probe population and zero non-probe fixture drift.",
            "Both combined tensors and aggregate manifests must reproduce byte-for-byte.",
            "The retry executes no teacher, model, optimizer, or source graph.",
            "The sealed tensors remain zero-credit teacher evidence and cannot ship in a Gamma codec.",
        ],
        "controls": [
            {"id": "sealed-capture-population", "role": "treatment", "definition": "Combine every declared state from both completed parent capture directories without recomputation."},
            {"id": "exact-probe-population", "role": "comparator", "definition": "Require exactly the input/adjoint, 64-state, bin/meta top_pre_ff_ paths in each manifest."},
            {"id": "non-probe-fixture-identity", "role": "shifted", "definition": "Require every non-probe path to match the retained fixture by size and digest."},
            {"id": "boundary-placement", "role": "negative", "definition": "Require the pre-normalization input and total adjoint to differ from their post-normalization branch counterparts."},
            {"id": "sealed-replay", "role": "replay", "definition": "Require both completed manifests and combined tensors to reproduce byte-for-byte."},
        ],
        "causalBoundary": {
            "availableInformation": [
                "The hash-bound failed job, guard, log, candidate revision, parent experiment, two completed capture directories, normalized branch operands, and retained fixture manifest."
            ],
            "forbiddenInformation": [
                "Teacher rerun, tensor modification, broad wildcard exclusion, tolerance, fitted correction, hidden trace use in an open implementation, or objective credit."
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
