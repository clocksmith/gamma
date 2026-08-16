#!/usr/bin/env python3
"""Freeze the production layer-19 GEGLU branch-adjoint capture."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_top_ff2_input_adjoint_64_q0_v1_materializer as parent
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_geglu_branch_adjoints_64_q0_v1"
PARENT_ID = "nncp_libnc_top_ff2_input_adjoint_64_q0_v1"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T090806227557Z_6c0a99aa4fc6.json"
)
PARENT_EXPERIMENT = ROOT / f"operations/adaptive/experiments/{PARENT_ID}.json"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T090818Z_428a8e6c62.json"
)
OPEN_ID = "nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v2"
OPEN_RESULT = ROOT / "results" / OPEN_ID
OPEN_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T095147Z_8ddedba49c.json"
)
FIXTURE_ROOT = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
RUNNER = ROOT / "tools/nncp_libnc_top_geglu_branch_adjoints_64_q0_v1.py"
MATERIALIZER = Path(__file__).resolve()
PROBE_SOURCE = ROOT / "tools/nncp_libnc_top_geglu_branch_probe_q0.c"
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
            "At least one production layer-19 GEGLU split-branch adjoint differs "
            "from the open branch residual even after the incoming FF2 residual "
            "is source-exact, localizing the retained ff_bias1_19 mismatch before "
            "bias projection."
        ),
        "falsification": (
            "If both complete branch adjoints equal their open counterparts, the "
            "GEGLU backward is exonerated and the mismatch is localized to bias "
            "projection. Any capture, replay, fixture, source, strict-output, or "
            "resource failure invalidates the attribution."
        ),
    }
    experiment["changedMechanism"] = (
        "Attach independent zero-valued marked parameters to the gate and value "
        "branches immediately after the production layer-19 GEGLU split, capture "
        "both inputs and both branch adjoints twice, then compare each adjoint with "
        "the corresponding half of the already-complete open FF1-output residual."
    )
    experiment["controls"] = [
        {
            "id": "production-fixture-identity",
            "role": "comparator",
            "definition": "Every non-probe fixture payload remains byte-identical to the retained production fixture in both executions.",
        },
        {
            "id": "independent-source-replay",
            "role": "replay",
            "definition": "Two complete source executions reproduce all four branch tensors and capture manifests byte-identically.",
        },
        {
            "id": "sealed-open-branches",
            "role": "treatment",
            "definition": "The open branch residuals are split from a sealed complete FF1-output residual only after both source captures exist.",
        },
        {
            "id": "nonzero-branch-adjoints",
            "role": "negative",
            "definition": "Both captured branch adjoints must differ from all-zero tensors so dead probes cannot pass equality.",
        },
    ]
    experiment["causalBoundary"] = {
        "availableInformation": [
            "Digest-bound source and fixture, the source-exact incoming FF2 residual verdict, the sealed open FF1-output residual, and frozen split-branch probe placement.",
            "Open branch residuals only as post-capture comparators after both complete source captures exist.",
        ],
        "forbiddenInformation": [
            "Using captured branch values as codec inputs, changing production arithmetic, fitting coordinate repairs, tolerance, future symbols, or teacher probabilities.",
            "Claiming an exact GEGLU implementation, bias-projection parity, recursive update, compression, transfer, package, or Hutter credit from this attribution alone.",
        ],
    }
    experiment["invariants"] = [
        "The two zero probes are attached only after the layer-19 GEGLU split at target block 256.",
        "Both source executions are complete and all non-probe fixture payloads remain identical.",
        "The sealed open FF1 residual is never a source-execution input.",
        "Gate and value branches remain separately identified through capture, combination, and comparison.",
        "Captured source tensors have zero objective and package credit.",
    ]
    experiment["budget"] = {
        "expectedGrossSavingsBytes": 0,
        "expectedNetSavingsBytes": -2_000_000,
        "maximumAddedPackageBytes": 2_000_000,
    }
    experiment["evidenceClass"] = "oracle"
    removed_ids = {
        "runner",
        "materializer",
        "probe-source",
        "open-decision",
        "open-execution",
        "open-guard",
        "open-reflection",
        "open-ff2-input-residual",
    }
    inputs = [item for item in experiment["inputs"] if item["id"] not in removed_ids]
    additions = [
        base.reference(RUNNER, "runner"),
        base.reference(MATERIALIZER, "materializer"),
        base.reference(PROBE_SOURCE, "probe-source"),
        base.reference(PARENT_RESULT / "decision.json", "parent-decision"),
        base.reference(PARENT_RESULT / "execution.json", "parent-execution"),
        base.reference(PARENT_RESULT / "guard.json", "parent-guard"),
        base.reference(PARENT_REFLECTION, "parent-reflection"),
        base.reference(OPEN_RESULT / "decision.json", "open-decision"),
        base.reference(OPEN_RESULT / "execution.json", "open-execution"),
        base.reference(OPEN_RESULT / "guard.json", "open-guard"),
        base.reference(OPEN_REFLECTION, "open-reflection"),
        base.reference(
            OPEN_RESULT / "open-ff1-output-residual.bf16",
            "open-ff1-output-residual",
        ),
        base.reference(FIXTURE_ROOT / "decision.json", "production-fixture-decision"),
        base.reference(
            FIXTURE_ROOT / "fixture-manifest.json", "production-fixture-manifest"
        ),
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
        measurement("branchInputElementCount", "BF16 elements", "Elements in each captured GEGLU branch input."),
        measurement("branchAdjointElementCount", "BF16 elements", "Elements in each captured GEGLU branch adjoint."),
        measurement("sourceCaptureDeterministic", "boolean", "Both complete source captures are byte-identical."),
        measurement("fixturePayloadIdentical", "boolean", "All non-probe fixture payloads match the retained fixture."),
        measurement("fixturePayloadMismatchCount", "files", "Non-probe fixture identity mismatches."),
        measurement("gateAdjointMismatchCount", "BF16 elements", "Source versus open gate-branch adjoint mismatches."),
        measurement("maximumGateAdjointAbsoluteError", "float32 value", "Maximum source versus open gate-branch error."),
        measurement("valueAdjointMismatchCount", "BF16 elements", "Source versus open value-branch adjoint mismatches."),
        measurement("maximumValueAdjointAbsoluteError", "float32 value", "Maximum source versus open value-branch error."),
        measurement("anyBranchAdjointMismatch", "boolean", "At least one source/open branch adjoint differs."),
        measurement("comparatorLive", "boolean", "Both source branch adjoints differ from all-zero bytes."),
        measurement("incrementalSourceBytes", "bytes", "Compressed source closure size."),
        measurement("guardedWorkRootPass", "boolean", "Candidate work root is removed before finalization."),
    ]
    experiment["promotionPredicates"] = [
        predicate("p-antecedents", "antecedentsPass", "eq", True),
        predicate("p-captures", "captureCount", "eq", 2),
        predicate("p-samples", "sampleCount", "eq", 2048),
        predicate("p-input-count", "branchInputElementCount", "eq", 6_291_456),
        predicate("p-adjoint-count", "branchAdjointElementCount", "eq", 6_291_456),
        predicate("p-replay", "sourceCaptureDeterministic", "eq", True),
        predicate("p-fixture", "fixturePayloadIdentical", "eq", True),
        predicate("p-fixture-mismatches", "fixturePayloadMismatchCount", "eq", 0),
        predicate("p-branch-mismatch", "anyBranchAdjointMismatch", "eq", True),
        predicate("p-live", "comparatorLive", "eq", True),
        predicate("p-source", "incrementalSourceBytes", "lte", 2_000_000),
        predicate("p-work-root", "guardedWorkRootPass", "eq", True),
    ]
    experiment["killPredicates"] = [
        predicate("k-antecedents", "antecedentsPass", "eq", True),
        predicate("k-replay", "sourceCaptureDeterministic", "eq", True),
        predicate("k-gate-exact", "gateAdjointMismatchCount", "eq", 0),
        predicate("k-value-exact", "valueAdjointMismatchCount", "eq", 0),
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
