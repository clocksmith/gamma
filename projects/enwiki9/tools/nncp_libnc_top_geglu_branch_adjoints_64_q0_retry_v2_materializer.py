#!/usr/bin/env python3
"""Freeze the sealed GEGLU manifest-accounting correction."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_top_geglu_branch_adjoints_64_q0_v1_materializer as parent
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_geglu_branch_adjoints_64_q0_retry_v2"
PARENT_ID = "nncp_libnc_top_geglu_branch_adjoints_64_q0_retry_v1"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T101116986368Z_9eb48e7bd66c.json"
)
PARENT_EXPERIMENT = ROOT / f"operations/adaptive/experiments/{PARENT_ID}.json"
SOURCE_RESULT = ROOT / "results" / PARENT_ID
SOURCE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T101128Z_dc16c55f42.json"
)
FIXTURE_MANIFEST = ROOT / (
    "results/nncp_libnc_profile_update_fixture_64_q3_v1/fixture-manifest.json"
)
RUNNER = ROOT / "tools/nncp_libnc_top_geglu_branch_adjoints_64_q0_retry_v2.py"
MATERIALIZER = Path(__file__).resolve()
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
base = parent.base


def measurement(identifier: str, unit: str, definition: str) -> dict[str, str]:
    return {"id": identifier, "unit": unit, "definition": definition}


def predicate(
    identifier: str,
    measurement_id: str,
    operator: str,
    threshold: int | bool,
) -> dict[str, object]:
    return {
        "id": identifier,
        "measurement": measurement_id,
        "operator": operator,
        "threshold": threshold,
    }


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
            "Excluding exactly the declared top_geglu_ probe namespace from both "
            "sealed manifests leaves zero non-probe fixture mismatches and validates "
            "the measured attribution: the value branch is exact while only the "
            "gate branch differs."
        ),
        "falsification": (
            "Any unexpected probe path, missing declared probe path, non-probe "
            "fixture mismatch, source-artifact drift, or strict-output failure "
            "prevents promotion."
        ),
    }
    experiment["changedMechanism"] = (
        "Do not rerun the teacher. Re-evaluate both sealed capture manifests while "
        "excluding exactly the prospectively declared top_geglu_ probe population, "
        "copy the four digest-bound branch artifacts, and preserve every scientific "
        "measurement and predicate."
    )
    experiment["controls"] = [
        {
            "id": "exact-probe-population",
            "role": "treatment",
            "definition": "Each sealed manifest must contain exactly the generated gate/value, input/adjoint, 64-state, bin/meta probe path set.",
        },
        {
            "id": "non-probe-fixture-identity",
            "role": "comparator",
            "definition": "Every path outside top_geglu_ must match the retained production fixture by size and digest in both captures.",
        },
        {
            "id": "sealed-branch-artifacts",
            "role": "replay",
            "definition": "The four source branch tensors are copied byte-for-byte from the completed guarded capture and never recomputed.",
        },
    ]
    experiment["causalBoundary"] = {
        "availableInformation": [
            "The sealed decision, execution manifests, guard, reflection, four branch tensors, retained fixture manifest, and declared top_geglu_ namespace.",
            "The previous scientific mismatch counts are preserved, not recomputed or tuned."
        ],
        "forbiddenInformation": [
            "Teacher execution, modifying branch tensors, broad wildcard exclusions, ignoring non-probe paths, tolerance, fitted corrections, or future symbols.",
            "Claiming an exact open GELU derivative, recursive update, compression, transfer, package, or Hutter credit from the corrected attribution."
        ],
    }
    experiment["invariants"] = [
        "Exactly 512 declared probe files must be present in each of two manifests.",
        "Every non-probe fixture file must match the retained fixture exactly.",
        "All four copied branch artifacts retain their sealed digests.",
        "The correction changes accounting only and has zero objective credit.",
    ]
    replacements = {
        "runner": base.reference(RUNNER, "runner"),
        "materializer": base.reference(MATERIALIZER, "materializer"),
    }
    inputs = [replacements.get(item["id"], item) for item in experiment["inputs"]]
    additions = [
        base.reference(SOURCE_RESULT / "decision.json", "source-decision"),
        base.reference(SOURCE_RESULT / "execution.json", "source-execution"),
        base.reference(SOURCE_RESULT / "guard.json", "source-guard"),
        base.reference(SOURCE_REFLECTION, "source-reflection"),
        base.reference(FIXTURE_MANIFEST, "production-fixture-manifest"),
        *(
            base.reference(SOURCE_RESULT / name, name.removesuffix(".bf16"))
            for name in (
                "source-geglu-gate-input.bf16",
                "source-geglu-gate-adjoint.bf16",
                "source-geglu-value-input.bf16",
                "source-geglu-value-adjoint.bf16",
            )
        ),
    ]
    existing_ids = {item["id"] for item in inputs}
    inputs.extend(item for item in additions if item["id"] not in existing_ids)
    present_paths = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present_paths:
            inputs.append(base.reference(path, base.source_identifier(path)))
            present_paths.add(relative)
    experiment["inputs"] = inputs
    experiment["measurements"].extend(
        [
            measurement("declaredProbeFileCount", "files", "Declared top_geglu_ probe files across both manifests."),
            measurement("declaredProbePopulationExact", "boolean", "Each manifest has exactly the declared probe path set."),
            measurement("recordedMismatchesAreDeclaredProbeOnly", "boolean", "Every mismatch recorded by the stale filter belongs to the declared probe set."),
        ]
    )
    experiment["promotionPredicates"].extend(
        [
            predicate("p-probe-file-count", "declaredProbeFileCount", "eq", 1024),
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
