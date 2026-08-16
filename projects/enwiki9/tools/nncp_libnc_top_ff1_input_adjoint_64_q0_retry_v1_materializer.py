#!/usr/bin/env python3
"""Freeze the sealed top-FF1 probe-accounting correction."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_ff1_input_adjoint_64_q0_retry_v1"
PARENT_ID = "nncp_libnc_top_ff1_input_adjoint_64_q0_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_EXPERIMENT = ROOT / f"operations/adaptive/experiments/{PARENT_ID}.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T121911Z_d066eaf1cf.json"
)
FIXTURE_MANIFEST = ROOT / (
    "results/nncp_libnc_profile_update_fixture_64_q3_v1/fixture-manifest.json"
)
RUNNER = ROOT / "tools/nncp_libnc_top_ff1_input_adjoint_64_q0_retry_v1.py"
MATERIALIZER = Path(__file__).resolve()
DESCRIPTOR = ROOT / "programs" / CANDIDATE_ID / "program.py"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
HYPOTHESIS = (
    "Excluding exactly the declared 256-file top_ff1_ probe population from "
    "each sealed capture leaves zero non-probe fixture mismatches while "
    "preserving the deterministic exact input, live adjoint, and initial BF16 "
    "matrix artifacts."
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


def measurement(identifier: str, unit: str, definition: str) -> dict[str, str]:
    return {"id": identifier, "unit": unit, "definition": definition}


def predicate(
    identifier: str, measurement_id: str, operator: str, threshold: object
) -> dict[str, object]:
    return {
        "id": identifier,
        "measurement": measurement_id,
        "operator": operator,
        "threshold": threshold,
    }


def source_identifier(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    suffix = hashlib.sha256(relative.encode()).hexdigest()[:12]
    return f"runtime-source-{path.stem}-{suffix}"


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    experiment = json.loads(PARENT_EXPERIMENT.read_text())
    parent_revision = ROOT / json.loads(
        (PARENT_RESULT / "decision.json").read_text()
    )["candidateRevision"]["receipt"]["path"]
    experiment["experimentId"] = CANDIDATE_ID
    experiment["proposalId"] = CANDIDATE_ID
    experiment["parent"] = {
        "candidateId": PARENT_ID,
        "revision": {
            key: value
            for key, value in reference(
                parent_revision, "parent-revision"
            ).items()
            if key != "id"
        },
    }
    experiment["hypothesis"] = {
        "claim": HYPOTHESIS,
        "falsification": "Any unexpected or missing declared probe path, non-probe fixture mismatch, source-artifact drift, strict-output failure, or resource failure rejects the correction.",
    }
    experiment["changedMechanism"] = (
        "Do not rerun the teacher. Re-evaluate both sealed capture manifests "
        "while excluding exactly the enumerated top_ff1_ input/adjoint, "
        "64-state, bin/meta probe population; copy the three bound tensor "
        "artifacts byte-for-byte and preserve every scientific measurement."
    )
    experiment["controls"] = [
        {
            "id": "exact-probe-population",
            "role": "treatment",
            "definition": "Each sealed manifest must contain exactly the 256 generated input/adjoint, 64-state, bin/meta probe paths.",
        },
        {
            "id": "non-probe-fixture-identity",
            "role": "comparator",
            "definition": "Every path outside the exact top_ff1_ set must match the retained production fixture by size and digest in both captures.",
        },
        {
            "id": "sealed-tensor-artifacts",
            "role": "replay",
            "definition": "The source input, source adjoint, and initial matrix are copied byte-for-byte from the completed guarded capture and never recomputed.",
        },
    ]
    experiment["causalBoundary"] = {
        "availableInformation": [
            "The sealed decision, execution manifests, guard, reflection, three tensor artifacts, retained fixture manifest, and exact declared path set.",
            "The previous scientific measurements are preserved, not recomputed or tuned."
        ],
        "forbiddenInformation": [
            "Teacher execution, tensor modification, broad wildcard exclusions, ignoring non-probe paths, tolerance, fitted corrections, or future symbols.",
            "Claiming an open transpose, compression improvement, transfer, package, or Hutter credit from corrected accounting."
        ],
    }
    experiment["invariants"] = [
        "Exactly 256 declared probe files must be present in each of two sealed manifests.",
        "Every non-probe fixture file must match the retained fixture exactly.",
        "All three copied tensor artifacts retain their sealed digests.",
        "The correction changes accounting only and has zero objective credit.",
    ]
    replacements = {
        "runner": reference(RUNNER, "runner"),
        "materializer": reference(MATERIALIZER, "materializer"),
        "program-descriptor": reference(DESCRIPTOR, "program-descriptor"),
    }
    inputs = [replacements.get(item["id"], item) for item in experiment["inputs"]]
    additions = [
        reference(PARENT_RESULT / "decision.json", "source-decision"),
        reference(PARENT_RESULT / "execution.json", "source-execution"),
        reference(PARENT_RESULT / "guard.json", "source-guard"),
        reference(PARENT_REFLECTION, "source-reflection"),
        reference(FIXTURE_MANIFEST, "production-fixture-manifest"),
        *(
            reference(PARENT_RESULT / name, name.removesuffix(".bf16"))
            for name in (
                "source-ff1-input.bf16",
                "source-ff1-input-adjoint.bf16",
                "source-initial-ff1-19.bf16",
            )
        ),
    ]
    existing_ids = {item["id"] for item in inputs}
    inputs.extend(item for item in additions if item["id"] not in existing_ids)
    present_paths = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present_paths:
            inputs.append(reference(path, source_identifier(path)))
            present_paths.add(relative)
    experiment["inputs"] = inputs
    experiment["measurements"].extend(
        [
            measurement("declaredProbeFileCount", "files", "Declared top_ff1_ probe files across both sealed manifests."),
            measurement("declaredProbePopulationExact", "boolean", "Each manifest has exactly the enumerated probe path set."),
            measurement("recordedMismatchesAreDeclaredProbeOnly", "boolean", "Every mismatch recorded by the stale filter belongs to the exact declared probe set."),
        ]
    )
    experiment["promotionPredicates"].extend(
        [
            predicate("p-probe-file-count", "declaredProbeFileCount", "eq", 512),
            predicate("p-probe-population", "declaredProbePopulationExact", "eq", True),
            predicate("p-recorded-probe-only", "recordedMismatchesAreDeclaredProbeOnly", "eq", True),
        ]
    )
    experiment["killPredicates"] = [
        predicate("k-antecedents", "antecedentsPass", "eq", True),
        predicate("k-non-probe-drift", "fixturePayloadMismatchCount", "gt", 0),
    ]
    experiment["outputs"] = [
        f"results/{CANDIDATE_ID}/decision.json",
        f"results/{CANDIDATE_ID}/execution.json",
        f"results/{CANDIDATE_ID}/source-ff1-input.bf16",
        f"results/{CANDIDATE_ID}/source-ff1-input-adjoint.bf16",
        f"results/{CANDIDATE_ID}/source-initial-ff1-19.bf16",
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
