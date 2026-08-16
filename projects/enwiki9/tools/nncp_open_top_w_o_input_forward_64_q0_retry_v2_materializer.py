#!/usr/bin/env python3
"""Freeze the receipt-only open pre-w_o salvage."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_open_top_w_o_input_forward_64_q0_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_w_o_input_forward_64_q0_retry_v2"
PARENT_ID = "nncp_open_top_w_o_input_forward_64_q0_retry_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T165727Z_496e36c06d.json"
)
PARENT_JOB = ROOT / (
    "operations/adaptive/failed/000_20260816T165727Z_496e36c06d.json"
)
PARENT_EXPERIMENT = ROOT / (
    "operations/adaptive/experiments/"
    "nncp_open_top_w_o_input_forward_64_q0_retry_v1.json"
)
SOURCE = ROOT / "results/nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1"
SOURCE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T162351Z_97a6519638.json"
)
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RUNNER = ROOT / "tools/nncp_open_top_w_o_input_forward_64_q0_retry_v2.py"
MATERIALIZER = Path(__file__).resolve()
DESCRIPTOR = PROGRAM / "program.py"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
SOURCE_CEILING = 300_000
HYPOTHESIS = (
    "A receipt-only salvage can independently revalidate the preserved exact "
    "layer-19 pre-w_o tensor, source comparison, live coordinate control, "
    "equal replay aggregates, exact layer checkpoints, dependency closure, "
    "and green resource envelope, then emit a contract-valid "
    "authorize-successor result without rerunning the forward population."
)


def source_identifier(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    suffix = hashlib.sha256(relative.encode()).hexdigest()[:12]
    return f"runtime-source-{path.stem}-{suffix}"


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    parent_revision = ROOT / json.loads(PARENT_REFLECTION.read_text())[
        "candidateRevision"
    ]["receipt"]["path"]
    inputs = [
        base.reference(
            PARENT_RESULT / "decision.prevalidation.json",
            "parent-prevalidation-result",
        ),
        base.reference(PARENT_RESULT / "execution.json", "parent-execution"),
        base.reference(PARENT_RESULT / "guard.json", "parent-guard"),
        base.reference(
            PARENT_RESULT / "open-exact-w-o-input.bf16",
            "parent-open-exact-w-o-input",
        ),
        base.reference(
            PARENT_RESULT / "incremental_source.tar.xz",
            "parent-incremental-source",
        ),
        base.reference(PARENT_EXPERIMENT, "parent-experiment"),
        base.reference(PARENT_JOB, "parent-failed-job"),
        base.reference(PARENT_REFLECTION, "parent-failure-reflection"),
        base.reference(SOURCE / "decision.json", "source-decision"),
        base.reference(SOURCE / "source-w-o-input.bf16", "source-w-o-input"),
        base.reference(SOURCE_REFLECTION, "source-reflection"),
        base.reference(RUNNER, "runner"),
        base.reference(MATERIALIZER, "materializer"),
        base.reference(DESCRIPTOR, "program-descriptor"),
    ]
    present = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present:
            inputs.append(base.reference(path, source_identifier(path)))
            present.add(relative)
    measurements = [
        base.measurement("antecedentsPass", "boolean", "The failed terminal job, reflection, preserved artifacts, and source oracle remain hash-bound."),
        base.measurement("parentBindingPass", "boolean", "The preserved result binds the frozen parent experiment and zero-credit objective."),
        base.measurement("preservedSciencePass", "boolean", "Every preserved scientific promotion predicate passed despite the invalid decision enum."),
        base.measurement("replayReceiptsPass", "boolean", "Both population aggregates, checkpoints, and 64 stream receipts agree exactly."),
        base.measurement("executionComparisonsPass", "boolean", "The preserved execution receipt records an exact treatment, live order control, and no forbidden dependency."),
        base.measurement("resourceEnvelopePass", "boolean", "The original expensive run stayed within memory and disk guards and failed only after result serialization."),
        base.measurement("preWOElementCount", "BF16 elements", "Words in the copied complete pre-w_o artifact."),
        base.measurement("independentSourceMismatchCount", "BF16 elements", "Copied treatment words differing under a fresh source comparison."),
        base.measurement("maximumIndependentAbsoluteError", "float32 value", "Maximum fresh treatment/oracle error."),
        base.measurement("streamMajorControlMismatchCount", "BF16 elements", "Preserved incorrect-order control words differing from the oracle."),
        base.measurement("artifactCopyExact", "boolean", "The salvaged artifact is byte-identical to the preserved treatment."),
        base.measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed receipt-salvage source."),
        base.measurement("guardedWorkRootPass", "boolean", "Transient salvage work was removed."),
    ]
    promotion = [
        base.predicate("p-antecedents", "antecedentsPass", "eq", True),
        base.predicate("p-parent-binding", "parentBindingPass", "eq", True),
        base.predicate("p-preserved-science", "preservedSciencePass", "eq", True),
        base.predicate("p-replay", "replayReceiptsPass", "eq", True),
        base.predicate("p-execution", "executionComparisonsPass", "eq", True),
        base.predicate("p-resources", "resourceEnvelopePass", "eq", True),
        base.predicate("p-elements", "preWOElementCount", "eq", 2097152),
        base.predicate("p-treatment", "independentSourceMismatchCount", "eq", 0),
        base.predicate("p-maximum", "maximumIndependentAbsoluteError", "eq", 0.0),
        base.predicate("p-control", "streamMajorControlMismatchCount", "gt", 0),
        base.predicate("p-copy", "artifactCopyExact", "eq", True),
        base.predicate("p-source", "incrementalSourceBytes", "lte", SOURCE_CEILING),
        base.predicate("p-work", "guardedWorkRootPass", "eq", True),
    ]
    experiment = {
        "schema": "gamma.enwiki9.adaptive-experiment-contract.v1",
        "objective": research_contracts.objective_binding(),
        "experimentId": CANDIDATE_ID,
        "proposalId": CANDIDATE_ID,
        "status": "frozen",
        "registrationTiming": "prospective",
        "evidenceClass": "oracle",
        "objectiveCreditBytes": 0,
        "parent": {
            "candidateId": PARENT_ID,
            "revision": {
                key: value
                for key, value in base.reference(
                    parent_revision, "parent-revision"
                ).items()
                if key != "id"
            },
        },
        "hypothesis": {
            "claim": HYPOTHESIS,
            "falsification": "Any artifact drift, fresh source mismatch, dead preserved control, unequal replay receipt, stale checkpoint, resource breach, or invalid successor result rejects salvage.",
        },
        "changedMechanism": "Replace the invalid descriptive decision enum with a receipt-only, contract-valid salvage that independently revalidates every preserved scientific and operational boundary.",
        "invariants": [
            "No open forward is rerun and no scientific value is recomputed except the independent artifact/source comparison.",
            "The preserved invalid result is evidence input only and is never presented as a valid terminal receipt.",
            "The copied tensor remains zero-credit oracle evidence with the same static GGML and fixture accounting boundary.",
        ],
        "controls": [
            {"id": "fresh-source-comparison", "role": "treatment", "definition": "Freshly compare every preserved treatment word to the independently captured source oracle."},
            {"id": "preserved-stream-major", "role": "comparator", "definition": "Require the prospectively frozen incorrect-order control to remain live in the preserved execution receipt."},
            {"id": "population-receipts", "role": "replay", "definition": "Require equal complete population aggregates and exact per-replay checkpoint receipts."},
        ],
        "population": {
            "unit": "BF16 layer-19 pre-w_o words",
            "scopeBytes": 4194304,
            "scopeSymbols": 2097152,
            "selection": "Every preserved feature for all 64 states and 32 production streams.",
            "coordinate": "state-major, stream-major, feature-major",
        },
        "causalBoundary": {
            "availableInformation": [
                "Only hash-bound artifacts and receipts completed before the parent serialization failure.",
                "The source oracle is opened only for a fresh full-population comparison under this frozen salvage contract.",
            ],
            "forbiddenInformation": [
                "Rerunning or editing forward outputs, fitting to mismatches, changing controls, tolerances, or rewriting the invalid parent result in place.",
                "Claiming compression gain, a dependency-free predictor, or Hutter objective credit.",
            ],
        },
        "budget": {
            "expectedGrossSavingsBytes": 0,
            "maximumAddedPackageBytes": SOURCE_CEILING,
            "expectedNetSavingsBytes": -SOURCE_CEILING,
        },
        "search": {
            "expectedTransferRetention": 1.0,
            "expectedRuntimeRatio": 0.01,
            "expectedMemoryRatio": 0.01,
            "uncertaintyRisk": 0.05,
            "interactionRisk": 0.05,
        },
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            base.predicate("k-antecedents", "antecedentsPass", "eq", True),
            base.predicate("k-treatment", "independentSourceMismatchCount", "gt", 0),
        ],
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/open-exact-w-o-input.bf16",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
        ],
        "outputManifestPolicy": "complete-result-artifacts-v1",
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
    OUTPUT.write_text(json.dumps(experiment, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(OUTPUT)
    print(OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
