#!/usr/bin/env python3
"""Freeze the production top pre-FF hidden-adjoint capture."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_v1"
PARENT_ID = "nncp_open_top_ff1_input_adjoint_block128_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_v1.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
DESCRIPTOR = PROGRAM / "program.py"
PROBE = ROOT / "tools/nncp_libnc_top_pre_ff_hidden_probe_q0.c"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T123635Z_f1f6615808.json"
)
NORMALIZED_INPUT = ROOT / (
    "results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1/"
    "open-ff1-input.bf16"
)
NORMALIZED_ADJOINT = PARENT_RESULT / "source-exact-ff1-input-adjoint.bf16"
FIXTURE = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
SOURCE_CEILING = 2_000_000
HYPOTHESIS = (
    "A marked zero node immediately before the layer-19 feed-forward split "
    "captures deterministic complete pre-normalization hidden input and total "
    "adjoint populations from both the direct residual and normalized FF "
    "branches without changing any non-probe fixture payload."
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
    parent_revision = ROOT / json.loads(
        (PARENT_RESULT / "decision.json").read_text()
    )["candidateRevision"]["receipt"]["path"]
    inputs = [
        reference(PARENT_RESULT / "decision.json", "parent-decision"),
        reference(PARENT_RESULT / "execution.json", "parent-execution"),
        reference(PARENT_RESULT / "guard.json", "parent-guard"),
        reference(PARENT_REFLECTION, "parent-reflection"),
        reference(NORMALIZED_INPUT, "normalized-ff1-input"),
        reference(NORMALIZED_ADJOINT, "normalized-ff1-input-adjoint"),
        reference(FIXTURE / "decision.json", "production-fixture-decision"),
        reference(
            FIXTURE / "fixture-manifest.json", "production-fixture-manifest"
        ),
        reference(FIXTURE / "guard.json", "production-fixture-guard"),
        reference(PROBE, "probe-source"),
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
    measurements = [
        measurement("antecedentsPass", "boolean", "The open FF1 input adjoint, production fixture, normalized operands, and source probe remain hash-bound."),
        measurement("captureCount", "captures", "Independent complete source capture populations."),
        measurement("sampleCount", "state-stream samples", "Chronological layer-19 pre-FF hidden samples."),
        measurement("hiddenElementCount", "BF16 elements", "Words in the combined source pre-FF hidden input."),
        measurement("adjointElementCount", "BF16 elements", "Words in the combined source pre-FF total adjoint."),
        measurement("sourceCaptureDeterministic", "boolean", "Two complete hidden and adjoint captures reproduce byte-for-byte."),
        measurement("declaredProbeFileCount", "files", "Exact input/adjoint, 64-state, bin/meta probe files across both captures."),
        measurement("declaredProbePopulationExact", "boolean", "Each manifest contains exactly the declared top_pre_ff_ probe path set."),
        measurement("nonProbeFixtureMismatchCount", "files", "Non-probe files differing from the retained production fixture across both captures."),
        measurement("fixturePayloadIdentical", "boolean", "Every non-probe fixture file retains its bound size and digest."),
        measurement("hiddenComparatorLive", "boolean", "The captured pre-FF hidden input is not all zero."),
        measurement("adjointComparatorLive", "boolean", "The captured total adjoint is not all zero."),
        measurement("preVsPostNormInputMismatchCount", "BF16 elements", "Pre-normalization hidden words differing from the exact normalized FF1 input."),
        measurement("totalVsNormBranchAdjointMismatchCount", "BF16 elements", "Total hidden-adjoint words differing from the normalized FF branch adjoint."),
        measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed oracle source."),
        measurement("guardedWorkRootPass", "boolean", "All transient build and capture payloads were removed."),
    ]
    promotion = [
        predicate("p-antecedents", "antecedentsPass", "eq", True),
        predicate("p-captures", "captureCount", "eq", 2),
        predicate("p-samples", "sampleCount", "eq", 2048),
        predicate("p-hidden-elements", "hiddenElementCount", "eq", 2097152),
        predicate("p-adjoint-elements", "adjointElementCount", "eq", 2097152),
        predicate("p-deterministic", "sourceCaptureDeterministic", "eq", True),
        predicate("p-probe-files", "declaredProbeFileCount", "eq", 512),
        predicate("p-probe-population", "declaredProbePopulationExact", "eq", True),
        predicate("p-fixture-count", "nonProbeFixtureMismatchCount", "eq", 0),
        predicate("p-fixture", "fixturePayloadIdentical", "eq", True),
        predicate("p-hidden-live", "hiddenComparatorLive", "eq", True),
        predicate("p-adjoint-live", "adjointComparatorLive", "eq", True),
        predicate("p-input-boundary", "preVsPostNormInputMismatchCount", "gt", 0),
        predicate("p-adjoint-boundary", "totalVsNormBranchAdjointMismatchCount", "gt", 0),
        predicate("p-source", "incrementalSourceBytes", "lte", SOURCE_CEILING),
        predicate("p-work-root", "guardedWorkRootPass", "eq", True),
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
                for key, value in reference(
                    parent_revision, "parent-revision"
                ).items()
                if key != "id"
            },
        },
        "hypothesis": {
            "claim": HYPOTHESIS,
            "falsification": "Any incomplete, nondeterministic, zero, fixture-changing, wrong-boundary, source-failing, or resource-failing capture rejects the oracle.",
        },
        "changedMechanism": "Attach one zero-valued marked tensor before the layer-19 ff_input duplication at production block 256, so its callback receives the sum of the direct residual and normalized feed-forward branch adjoints.",
        "invariants": [
            "The production block, model, source tree, library, parameters, state, optimizer, gradients, probabilities, and update remain unchanged.",
            "The marked zero tensor changes no forward value and is upstream of both feed-forward branches.",
            "Each capture manifest must contain exactly the declared top_pre_ff_ input/adjoint files and zero non-probe drift.",
            "The captured tensors are zero-credit teacher evidence and cannot ship in a Gamma codec.",
        ],
        "controls": [
            {"id": "marked-zero-total-adjoint", "role": "treatment", "definition": "Attach one marked zero before the top feed-forward split and capture its complete callback gradient."},
            {"id": "normalized-ff-input", "role": "shifted", "definition": "Require the pre-normalization input to differ from the independently exact post-normalization FF1 operand."},
            {"id": "normalized-branch-adjoint", "role": "negative", "definition": "Require the total adjoint to differ from the exact normalized FF branch adjoint, proving inclusion of the direct residual branch."},
            {"id": "exact-probe-population", "role": "comparator", "definition": "Exclude only the exact declared probe paths and require all other fixture files to retain their bound digests."},
            {"id": "independent-replay", "role": "replay", "definition": "Repeat the complete source capture and compare both tensors and manifests byte-for-byte."},
        ],
        "population": {
            "unit": "BF16 layer-19 pre-FF hidden-adjoint words",
            "scopeBytes": 4194304,
            "scopeSymbols": 2097152,
            "selection": "Every one of 1,024 features for all 64 chronological states and 32 streams at production block 256.",
            "coordinate": "state-major, stream-major, feature-major",
        },
        "causalBoundary": {
            "availableInformation": [
                "The bound production graph and update callback.",
                "The exact normalized FF1 input and its exact open adjoint for boundary-placement controls.",
                "The exact declared probe namespace and retained fixture manifest.",
            ],
            "forbiddenInformation": [
                "The captured tensors during future open-kernel tuning, coordinate repair, tolerance, or any hidden trace in a submitted codec."
            ],
        },
        "budget": {
            "expectedGrossSavingsBytes": 0,
            "maximumAddedPackageBytes": SOURCE_CEILING,
            "expectedNetSavingsBytes": -SOURCE_CEILING,
        },
        "search": {
            "expectedTransferRetention": 0.0,
            "expectedRuntimeRatio": 1.0,
            "expectedMemoryRatio": 1.0,
            "uncertaintyRisk": 0.1,
            "interactionRisk": 0.1,
        },
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            predicate("k-antecedents", "antecedentsPass", "eq", True),
            predicate("k-adjoint-live", "adjointComparatorLive", "eq", False),
        ],
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/source-pre-ff-hidden.bf16",
            f"results/{CANDIDATE_ID}/source-pre-ff-hidden-adjoint.bf16",
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
