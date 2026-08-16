#!/usr/bin/env python3
"""Freeze the production FF2-input adjoint attribution gate."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_final_rmsnorm_reduction_scale_64_q0_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_ff2_input_adjoint_64_q0_v1"
PARENT_ID = "nncp_open_profile_top_ff1_bias_gradient_64_q0_v1"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T084738538470Z_6b8e56c63be9.json"
)
OPEN_RESULT = ROOT / "results" / PARENT_ID
OPEN_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T084751Z_2949ede196.json"
)
FIXTURE_ID = "nncp_libnc_profile_update_fixture_64_q3_v1"
FIXTURE_ROOT = ROOT / "results" / FIXTURE_ID
RUNNER = ROOT / "tools/nncp_libnc_top_ff2_input_adjoint_64_q0_v1.py"
MATERIALIZER = Path(__file__).resolve()
PROBE_SOURCE = ROOT / "tools/nncp_libnc_top_ff2_input_probe_q0.c"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"


def measurement(identifier: str, unit: str, definition: str) -> dict[str, str]:
    return {"id": identifier, "unit": unit, "definition": definition}


def predicate(
    identifier: str, measurement_id: str, operator: str, threshold: int | bool
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
    experiment = json.loads(
        (ROOT / "operations/adaptive/experiments/nncp_libnc_top_ff2_adjoint_64_q0_retry_v1.json").read_text()
    )
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
            "The complete production BF16 adjoint at the layer-19 GEGLU output "
            "is byte-identical to the open streaming-dot ff2_19 transpose "
            "residual, localizing the remaining ff_bias1_19 discrepancy strictly "
            "to GEGLU backward or its later projection."
        ),
        "falsification": (
            "Any source/open residual mismatch refutes the transpose contract; "
            "any capture, replay, fixture-identity, source, strict-output, or "
            "resource failure invalidates the attribution."
        ),
    }
    experiment["changedMechanism"] = (
        "Attach one zero-valued marked parameter to the production layer-19 "
        "GEGLU output before ff2_19, capture its complete backward adjoint twice, "
        "and compare it directly with the already-complete open FF2-input residual."
    )
    experiment["controls"] = [
        {
            "id": "production-fixture-identity",
            "role": "comparator",
            "definition": "Every non-probe source fixture payload remains byte-identical to the retained production fixture in both executions.",
        },
        {
            "id": "independent-source-replay",
            "role": "replay",
            "definition": "Two complete source executions reproduce identical inputs, adjoints, and capture manifests.",
        },
        {
            "id": "open-transpose-residual",
            "role": "treatment",
            "definition": "The open residual was completed and sealed before this source capture and is used only as a post-capture comparator.",
        },
        {
            "id": "nonzero-adjoint",
            "role": "negative",
            "definition": "The captured adjoint must differ from an all-zero tensor so a dead probe cannot pass equality accidentally.",
        },
    ]
    experiment["causalBoundary"] = {
        "availableInformation": [
            "Digest-bound source, initial production fixture, open transpose artifact, and frozen probe placement.",
            "The open residual only after both complete source adjoints exist.",
        ],
        "forbiddenInformation": [
            "Using captured adjoints as codec inputs, modifying production arithmetic, fitting corrections, tolerance, future symbols, or teacher probabilities.",
            "Claiming GEGLU parity, ff1_19 gradient parity, recursive update, compression, transfer, package, or Hutter progress from this attribution alone.",
        ],
    }
    experiment["invariants"] = [
        "The zero probe is attached before ff2_19 only at layer 19 and target block 256.",
        "Both source executions are complete and all non-probe fixture files remain identical.",
        "The open residual is never a source-execution input.",
        "Captured source tensors have zero objective and package credit.",
    ]
    experiment["budget"] = {
        "expectedGrossSavingsBytes": 0,
        "expectedNetSavingsBytes": -2_000_000,
        "maximumAddedPackageBytes": 2_000_000,
    }
    experiment["evidenceClass"] = "oracle"
    inputs = [
        item
        for item in experiment["inputs"]
        if item["id"] not in {
            "runner",
            "materializer",
            "probe-source",
            "reducer-source",
            "parent-open-decision",
            "parent-open-reflection",
            "parent-open-residual",
        }
    ]
    additions = [
        base.reference(RUNNER, "runner"),
        base.reference(MATERIALIZER, "materializer"),
        base.reference(PROBE_SOURCE, "probe-source"),
        base.reference(OPEN_RESULT / "decision.json", "open-decision"),
        base.reference(OPEN_RESULT / "execution.json", "open-execution"),
        base.reference(OPEN_RESULT / "guard.json", "open-guard"),
        base.reference(OPEN_REFLECTION, "open-reflection"),
        base.reference(
            OPEN_RESULT / "open-ff2-input-residual.bf16",
            "open-ff2-input-residual",
        ),
        base.reference(FIXTURE_ROOT / "decision.json", "production-fixture-decision"),
        base.reference(FIXTURE_ROOT / "fixture-manifest.json", "production-fixture-manifest"),
        base.reference(FIXTURE_ROOT / "guard.json", "production-fixture-guard"),
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
    experiment["measurements"] = [
        measurement("antecedentsPass", "boolean", "All bound source and open antecedents authorize capture."),
        measurement("captureCount", "executions", "Independent complete source captures."),
        measurement("sampleCount", "samples", "Captured production state-stream pairs."),
        measurement("sourceInputElementCount", "BF16 elements", "Captured GEGLU output population."),
        measurement("sourceAdjointElementCount", "BF16 elements", "Captured GEGLU-output adjoint population."),
        measurement("sourceCaptureDeterministic", "boolean", "Both source captures are byte-identical."),
        measurement("fixturePayloadIdentical", "boolean", "All non-probe source fixture payloads match the retained fixture."),
        measurement("fixturePayloadMismatchCount", "files", "Non-probe fixture identity mismatches."),
        measurement("openResidualMismatchCount", "BF16 elements", "Source versus open FF2-input residual mismatches."),
        measurement("maximumOpenResidualAbsoluteError", "float32 value", "Maximum source versus open residual error."),
        measurement("comparatorLive", "boolean", "Captured adjoint differs from all-zero bytes."),
        measurement("incrementalSourceBytes", "bytes", "Compressed source closure size."),
        measurement("guardedWorkRootPass", "boolean", "Candidate work root is removed before finalization."),
    ]
    experiment["promotionPredicates"] = [
        predicate("p-antecedents", "antecedentsPass", "eq", True),
        predicate("p-captures", "captureCount", "eq", 2),
        predicate("p-samples", "sampleCount", "eq", 2048),
        predicate("p-input-count", "sourceInputElementCount", "eq", 6_291_456),
        predicate("p-adjoint-count", "sourceAdjointElementCount", "eq", 6_291_456),
        predicate("p-replay", "sourceCaptureDeterministic", "eq", True),
        predicate("p-fixture", "fixturePayloadIdentical", "eq", True),
        predicate("p-fixture-mismatches", "fixturePayloadMismatchCount", "eq", 0),
        predicate("p-open-mismatch", "openResidualMismatchCount", "eq", 0),
        predicate("p-open-maximum", "maximumOpenResidualAbsoluteError", "eq", 0),
        predicate("p-live", "comparatorLive", "eq", True),
        predicate("p-source", "incrementalSourceBytes", "lte", 2_000_000),
        predicate("p-work-root", "guardedWorkRootPass", "eq", True),
    ]
    experiment["killPredicates"] = [
        predicate("k-antecedents", "antecedentsPass", "eq", True),
        predicate("k-open-mismatch", "openResidualMismatchCount", "gt", 0),
    ]
    experiment["outputs"] = [
        f"results/{CANDIDATE_ID}/decision.json",
        f"results/{CANDIDATE_ID}/execution.json",
        f"results/{CANDIDATE_ID}/source-ff2-input.bf16",
        f"results/{CANDIDATE_ID}/source-ff2-input-adjoint.bf16",
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
