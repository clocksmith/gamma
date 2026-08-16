#!/usr/bin/env python3
"""Freeze the source pre-FF normalization-branch adjoint oracle."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_open_top_pre_ff_rmsnorm_backward_64_q0_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_v1"
PARENT_ID = "nncp_open_top_pre_ff_residual_conversion_order_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
DESCRIPTOR = PROGRAM / "program.py"
PROBE = ROOT / "tools/nncp_libnc_top_pre_ff_norm_branch_probe_q0.c"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T135007Z_c0fde22dd2.json"
)
OPEN_RESULT = ROOT / (
    "results/nncp_open_top_pre_ff_rmsnorm_backward_state_reduce_64_q0_v1"
)
SOURCE_RESULT = ROOT / (
    "results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2"
)
FIXTURE = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
SOURCE_CEILING = 2_000_000


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    parent_revision = ROOT / json.loads(
        (PARENT_RESULT / "decision.json").read_text()
    )["candidateRevision"]["receipt"]["path"]
    inputs = [
        base.reference(PARENT_RESULT / "decision.json", "parent-decision"),
        base.reference(PARENT_RESULT / "execution.json", "parent-execution"),
        base.reference(PARENT_RESULT / "guard.json", "parent-guard"),
        base.reference(PARENT_REFLECTION, "parent-reflection"),
        base.reference(
            OPEN_RESULT / "open-pre-ff-norm-input-adjoint.bf16",
            "open-normalization-branch-adjoint",
        ),
        base.reference(
            SOURCE_RESULT / "source-pre-ff-hidden.bf16",
            "source-pre-ff-hidden",
        ),
        base.reference(
            SOURCE_RESULT / "source-pre-ff-hidden-adjoint.bf16",
            "source-pre-ff-total-adjoint",
        ),
        base.reference(FIXTURE / "decision.json", "fixture-decision"),
        base.reference(FIXTURE / "fixture-manifest.json", "fixture-manifest"),
        base.reference(FIXTURE / "guard.json", "fixture-guard"),
        base.reference(PROBE, "probe-source"),
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
            "claim": (
                "A marked-zero node placed only on the layer-19 pre-FF "
                "normalization branch yields a deterministic complete source "
                "adjoint that distinguishes branch-backward arithmetic from "
                "residual-join accumulation."
            ),
            "falsification": (
                "Any incomplete, nondeterministic, fixture-changing, dead, "
                "wrong-input, source-failing, or resource-failing capture "
                "rejects the oracle; source/open equality is measured rather "
                "than required."
            ),
        },
        "changedMechanism": (
            "Duplicate the layer-19 direct residual first, then attach one "
            "zero-valued marked tensor only to the pre-FF normalization input "
            "and capture that node's complete source adjoint twice."
        ),
        "invariants": [
            "The production source, target block, model, parameters, optimizer, gradients, probabilities, and update remain unchanged.",
            "The marked zero changes no forward value and is absent from the already-duplicated direct residual branch.",
            "Each capture contains exactly the declared branch input and adjoint files with zero non-probe fixture drift.",
            "The open branch artifact is used only after both source populations exist and no comparison result changes the captured tensors.",
            "All captured source tensors remain zero-credit teacher evidence and cannot ship in a Gamma codec.",
        ],
        "controls": [
            {
                "id": "normalization-only-marked-zero",
                "role": "treatment",
                "definition": "Attach the marked zero after the direct residual duplication and before layer-19 pre-FF normalization.",
            },
            {
                "id": "independent-source-replay",
                "role": "replay",
                "definition": "Repeat the complete source execution and require both tensors and manifests to be byte-identical.",
            },
            {
                "id": "exact-fixture-identity",
                "role": "comparator",
                "definition": "Exclude only the exact declared probe paths and require every other fixture file to retain its bound digest.",
            },
            {
                "id": "pre-ff-input-identity",
                "role": "shifted",
                "definition": "Require the branch probe input to equal the independently sealed pre-FF hidden input exactly.",
            },
            {
                "id": "total-adjoint-separation",
                "role": "negative",
                "definition": "Require the branch-only adjoint to differ from the sealed total adjoint so an upstream or misplaced probe cannot pass.",
            },
            {
                "id": "open-branch-comparator",
                "role": "treatment",
                "definition": "Measure exact source/open branch mismatch only after both complete source captures exist; either result selects the next boundary.",
            },
        ],
        "causalBoundary": {
            "availableInformation": [
                "Digest-bound source, production fixture, sealed pre-FF input and total adjoint, frozen probe placement, and the previously materialized open branch adjoint.",
                "The open branch comparator only after both complete source adjoints exist.",
            ],
            "forbiddenInformation": [
                "Using source adjoints as codec inputs, fitting coordinate corrections, tolerance, future symbols, teacher probabilities, or objective credit.",
                "Claiming recursive-update parity, compression improvement, transfer, package compliance, or Hutter progress from this oracle alone.",
            ],
        },
        "population": {
            "unit": "BF16 layer-19 pre-FF normalization-branch adjoint words",
            "scopeBytes": 4_194_304,
            "scopeSymbols": 2_097_152,
            "selection": "Every one of 1,024 features for all 64 chronological states and 32 streams at production block 256.",
            "coordinate": "state-major, stream-major, feature-major",
        },
        "measurements": [
            base.measurement("antecedentsPass", "boolean", "All source, fixture, open, and parent receipts remain hash-bound."),
            base.measurement("captureCount", "captures", "Independent complete source capture populations."),
            base.measurement("sampleCount", "state-stream samples", "Chronological layer-19 pre-FF samples."),
            base.measurement("inputElementCount", "BF16 elements", "Words in the combined normalization input."),
            base.measurement("adjointElementCount", "BF16 elements", "Words in the combined normalization-branch adjoint."),
            base.measurement("sourceCaptureDeterministic", "boolean", "Both complete source populations reproduce byte-for-byte."),
            base.measurement("declaredProbeFileCount", "files", "Exact input/adjoint, 64-state, bin/meta files across both captures."),
            base.measurement("declaredProbePopulationExact", "boolean", "Each manifest contains exactly the enumerated probe path set."),
            base.measurement("nonProbeFixtureMismatchCount", "files", "Non-probe files differing from the retained fixture across both captures."),
            base.measurement("inputMismatchCount", "BF16 elements", "Source branch-input words differing from the sealed pre-FF hidden input."),
            base.measurement("openBranchMismatchCount", "BF16 elements", "Source branch-adjoint words differing from the open formula."),
            base.measurement("maximumOpenBranchAbsoluteError", "float32 value", "Maximum source/open branch-adjoint error."),
            base.measurement("totalAdjointControlMismatchCount", "BF16 elements", "Branch-only words differing from the sealed total adjoint."),
            base.measurement("adjointComparatorLive", "boolean", "The captured branch adjoint is not all zero."),
            base.measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed oracle source."),
            base.measurement("guardedWorkRootPass", "boolean", "All transient build and capture payloads were removed."),
        ],
        "promotionPredicates": [
            base.predicate("p-antecedents", "antecedentsPass", "eq", True),
            base.predicate("p-captures", "captureCount", "eq", 2),
            base.predicate("p-samples", "sampleCount", "eq", 2_048),
            base.predicate("p-input-elements", "inputElementCount", "eq", 2_097_152),
            base.predicate("p-adjoint-elements", "adjointElementCount", "eq", 2_097_152),
            base.predicate("p-replay", "sourceCaptureDeterministic", "eq", True),
            base.predicate("p-probe-files", "declaredProbeFileCount", "eq", 512),
            base.predicate("p-probe-population", "declaredProbePopulationExact", "eq", True),
            base.predicate("p-fixture", "nonProbeFixtureMismatchCount", "eq", 0),
            base.predicate("p-input", "inputMismatchCount", "eq", 0),
            base.predicate("p-total-separation", "totalAdjointControlMismatchCount", "gt", 0),
            base.predicate("p-live", "adjointComparatorLive", "eq", True),
            base.predicate("p-source", "incrementalSourceBytes", "lte", SOURCE_CEILING),
            base.predicate("p-work-root", "guardedWorkRootPass", "eq", True),
        ],
        "killPredicates": [
            base.predicate("k-antecedents", "antecedentsPass", "eq", True),
            base.predicate("k-input", "inputMismatchCount", "gt", 0),
        ],
        "budget": {
            "expectedGrossSavingsBytes": 0,
            "maximumAddedPackageBytes": SOURCE_CEILING,
            "expectedNetSavingsBytes": -SOURCE_CEILING,
        },
        "search": {
            "expectedTransferRetention": 1.0,
            "expectedRuntimeRatio": 1.0,
            "expectedMemoryRatio": 0.9,
            "uncertaintyRisk": 0.05,
            "interactionRisk": 0.05,
        },
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/source-pre-ff-norm-input.bf16",
            f"results/{CANDIDATE_ID}/source-pre-ff-norm-branch-adjoint.bf16",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
        ],
        "outputManifestPolicy": "complete-result-artifacts-v1",
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
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
