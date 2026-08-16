#!/usr/bin/env python3
"""Freeze the production layer-19 w_o input-adjoint source oracle."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_w_o_input_adjoint_64_q0_v1"
PARENT_ID = "nncp_open_top_pre_ff_total_adjoint_64_q0_retry_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T155508Z_53d5388d2c.json"
)
PARENT_ADJOINT = PARENT_RESULT / "source-exact-pre-ff-total-adjoint.bf16"
FIXTURE = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
RUNNER = ROOT / "tools/nncp_libnc_top_w_o_input_adjoint_64_q0_v1.py"
MATERIALIZER = Path(__file__).resolve()
PROBE = ROOT / "tools/nncp_libnc_top_w_o_input_probe_q0.c"
DESCRIPTOR = ROOT / "programs" / CANDIDATE_ID / "program.py"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
SOURCE_CEILING = 2_000_000
HYPOTHESIS = (
    "A marked zero node immediately before the production layer-19 w_o matmul "
    "captures deterministic complete pre-w_o values and input adjoints without "
    "changing any non-probe fixture payload, while the initial w_o_19 BF16 "
    "matrix is extracted verbatim from the bound parameter container."
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
        reference(PARENT_ADJOINT, "parent-pre-w-o-output-adjoint"),
        reference(FIXTURE / "decision.json", "production-fixture-decision"),
        reference(FIXTURE / "fixture-manifest.json", "production-fixture-manifest"),
        reference(FIXTURE / "guard.json", "production-fixture-guard"),
        reference(
            FIXTURE / "fixture/parameters_initial.coefs",
            "production-initial-parameters",
        ),
        reference(
            FIXTURE / "fixture/gradients/0007_w_o_19.bin",
            "retained-w-o-gradient",
        ),
        reference(
            FIXTURE / "fixture/gradients/0007_w_o_19.meta",
            "retained-w-o-gradient-meta",
        ),
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
        measurement("antecedentsPass", "boolean", "The exact pre-FF parent, production fixture, retained w_o gradient, source tree, and probe remain hash-bound."),
        measurement("captureCount", "captures", "Independent complete source capture populations."),
        measurement("sampleCount", "state-stream samples", "Chronological pre-w_o input and adjoint samples."),
        measurement("sourceInputElementCount", "BF16 elements", "Words in the combined production pre-w_o input."),
        measurement("sourceAdjointElementCount", "BF16 elements", "Words in the combined production pre-w_o input adjoint."),
        measurement("initialMatrixElementCount", "BF16 elements", "Words extracted directly from the initial w_o_19 payload."),
        measurement("sourceCaptureDeterministic", "boolean", "Two complete source input and adjoint captures reproduce byte-for-byte."),
        measurement("declaredProbeFileCount", "files", "Declared top_w_o probe files across both captures."),
        measurement("declaredProbePopulationExact", "boolean", "Each capture has exactly the enumerated input/adjoint, state, and bin/meta probe paths."),
        measurement("fixturePayloadIdentical", "boolean", "Every non-probe production fixture payload is unchanged in both captures."),
        measurement("fixturePayloadMismatchCount", "files", "Non-probe fixture payload mismatches across both captures."),
        measurement("inputLive", "boolean", "The source pre-w_o input is not all zero."),
        measurement("adjointLive", "boolean", "The source pre-w_o input adjoint is not all zero."),
        measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed oracle source."),
        measurement("guardedWorkRootPass", "boolean", "Transient builds and raw capture payloads were removed only after a schema-valid pre-cleanup receipt existed."),
    ]
    promotion = [
        predicate("p-antecedents", "antecedentsPass", "eq", True),
        predicate("p-captures", "captureCount", "eq", 2),
        predicate("p-samples", "sampleCount", "eq", 2048),
        predicate("p-input-elements", "sourceInputElementCount", "eq", 2097152),
        predicate("p-adjoint-elements", "sourceAdjointElementCount", "eq", 2097152),
        predicate("p-matrix-elements", "initialMatrixElementCount", "eq", 1048576),
        predicate("p-deterministic", "sourceCaptureDeterministic", "eq", True),
        predicate("p-probe-files", "declaredProbeFileCount", "eq", 512),
        predicate("p-probe-population", "declaredProbePopulationExact", "eq", True),
        predicate("p-fixture", "fixturePayloadIdentical", "eq", True),
        predicate("p-fixture-count", "fixturePayloadMismatchCount", "eq", 0),
        predicate("p-input-live", "inputLive", "eq", True),
        predicate("p-adjoint-live", "adjointLive", "eq", True),
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
            "falsification": "Any incomplete, nondeterministic, zero, fixture-changing, conversion-changing, source-failing, or resource-failing capture rejects the oracle.",
        },
        "changedMechanism": "Attach one zero-valued marked tensor immediately after concat_head and before only the layer-19 w_o matmul at production block 256; enumerate its exact probe namespace, capture its callback adjoint, and extract the initial w_o_19 BF16 payload verbatim.",
        "invariants": [
            "The production block, model, source tree, library, parameters, state, optimizer, gradients, probabilities, and update remain unchanged.",
            "The marked zero tensor changes no forward value and is consumed only as an adjoint oracle.",
            "All 64 states and 32 streams are captured in chronological state-stream order twice.",
            "The initial w_o_19 matrix is copied from the bound BF16 container payload without conversion.",
            "The captured tensors are zero-credit teacher evidence and cannot ship in a Gamma codec.",
        ],
        "controls": [
            {"id": "marked-zero-adjoint", "role": "treatment", "definition": "Attach one marked zero tensor before w_o_19 and capture its complete callback gradient."},
            {"id": "exact-probe-population", "role": "comparator", "definition": "Require exactly the enumerated 256 generated probe paths in each capture."},
            {"id": "unchanged-fixture", "role": "shifted", "definition": "Require every non-probe production fixture payload to retain its bound digest."},
            {"id": "live-tensors", "role": "negative", "definition": "Reject an all-zero input or adjoint."},
            {"id": "independent-replay", "role": "replay", "definition": "Repeat the complete source capture and compare both tensors byte-for-byte."},
        ],
        "population": {
            "unit": "BF16 layer-19 pre-w_o input-adjoint words",
            "scopeBytes": 4194304,
            "scopeSymbols": 2097152,
            "selection": "Every one of 1,024 features for all 64 chronological states and 32 streams at production block 256.",
            "coordinate": "state-major, stream-major, feature-major",
        },
        "causalBoundary": {
            "availableInformation": [
                "The bound production graph and update callback.",
                "The exact open post-w_o output adjoint, retained w_o_19 gradient, and initial parameter container are bound for successor validation but are not used to judge this capture.",
            ],
            "forbiddenInformation": [
                "The captured input or adjoint during any future open-kernel implementation or tuning.",
                "Any hidden trace, source oracle, or retained tensor in a submitted codec.",
                "Claiming open parity, compression improvement, or Hutter credit from this source capture.",
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
            predicate("k-fixture-drift", "fixturePayloadMismatchCount", "gt", 0),
        ],
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/source-w-o-input.bf16",
            f"results/{CANDIDATE_ID}/source-w-o-input-adjoint.bf16",
            f"results/{CANDIDATE_ID}/source-initial-w-o-19.bf16",
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
