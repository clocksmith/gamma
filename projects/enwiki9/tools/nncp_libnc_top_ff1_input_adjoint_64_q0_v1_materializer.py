#!/usr/bin/env python3
"""Freeze the production top-FF1 input-adjoint capture."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_ff1_input_adjoint_64_q0_v1"
PARENT_ID = "nncp_open_profile_top_ff1_gradient_post_add_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_libnc_top_ff1_input_adjoint_64_q0_v1.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
DESCRIPTOR = PROGRAM / "program.py"
PROBE = ROOT / "tools/nncp_libnc_top_ff1_input_probe_q0.c"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T121133Z_b2c70f9ec5.json"
)
OPEN_INPUT = ROOT / (
    "results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1/"
    "open-ff1-input.bf16"
)
OPEN_OUTPUT_ADJOINT = ROOT / (
    "results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/"
    "open-ff1-output-residual.bf16"
)
FIXTURE = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
PARENT_REVISION = ROOT / json.loads((PARENT_RESULT / "decision.json").read_text())[
    "candidateRevision"
]["receipt"]["path"]
SOURCE_CEILING = 2_000_000
HYPOTHESIS = (
    "A marked zero node immediately before the production ff1_19 matmul "
    "captures deterministic complete FF1 input and adjoint populations without "
    "changing fixture payloads; the source forward input matches the exact open "
    "input and the initial BF16 matrix is extracted without conversion."
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
    inputs = [
        reference(PARENT_RESULT / "decision.json", "open-decision"),
        reference(PARENT_RESULT / "execution.json", "open-execution"),
        reference(PARENT_RESULT / "guard.json", "open-guard"),
        reference(PARENT_REFLECTION, "open-reflection"),
        reference(OPEN_INPUT, "open-ff1-input"),
        reference(OPEN_OUTPUT_ADJOINT, "open-ff1-output-adjoint"),
        reference(FIXTURE / "decision.json", "production-fixture-decision"),
        reference(FIXTURE / "fixture-manifest.json", "production-fixture-manifest"),
        reference(FIXTURE / "guard.json", "production-fixture-guard"),
        reference(
            FIXTURE / "fixture/parameters_initial.coefs",
            "production-initial-parameters",
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
        measurement("antecedentsPass", "boolean", "The open FF1 boundary, production fixture, exact operands, and source probe remain hash-bound."),
        measurement("captureCount", "captures", "Independent complete source capture populations."),
        measurement("sampleCount", "state-stream samples", "Chronological FF1 input and adjoint samples."),
        measurement("sourceInputElementCount", "BF16 elements", "Words in the combined production FF1 input."),
        measurement("sourceAdjointElementCount", "BF16 elements", "Words in the combined production FF1 input adjoint."),
        measurement("initialMatrixElementCount", "BF16 elements", "Words extracted directly from the initial ff1_19 parameter payload."),
        measurement("sourceInputMismatchCount", "BF16 elements", "Production FF1-input words differing from the exact open forward operand."),
        measurement("maximumSourceInputAbsoluteError", "float32 value", "Maximum source/open FF1-input error."),
        measurement("sourceCaptureDeterministic", "boolean", "Two complete source input and adjoint captures reproduce byte-for-byte."),
        measurement("fixturePayloadIdentical", "boolean", "All production fixture payloads remain identical to the retained run."),
        measurement("fixturePayloadMismatchCount", "files", "Production fixture files whose payload differs."),
        measurement("comparatorLive", "boolean", "The captured source input adjoint is not all zero."),
        measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed oracle source."),
        measurement("guardedWorkRootPass", "boolean", "All transient build and capture payloads were removed."),
    ]
    promotion = [
        predicate("p-antecedents", "antecedentsPass", "eq", True),
        predicate("p-captures", "captureCount", "eq", 2),
        predicate("p-samples", "sampleCount", "eq", 2048),
        predicate("p-input-elements", "sourceInputElementCount", "eq", 2097152),
        predicate("p-adjoint-elements", "sourceAdjointElementCount", "eq", 2097152),
        predicate("p-matrix-elements", "initialMatrixElementCount", "eq", 6291456),
        predicate("p-input", "sourceInputMismatchCount", "eq", 0),
        predicate("p-input-maximum", "maximumSourceInputAbsoluteError", "eq", 0.0),
        predicate("p-deterministic", "sourceCaptureDeterministic", "eq", True),
        predicate("p-fixture", "fixturePayloadIdentical", "eq", True),
        predicate("p-fixture-count", "fixturePayloadMismatchCount", "eq", 0),
        predicate("p-live", "comparatorLive", "eq", True),
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
                    PARENT_REVISION, "parent-revision"
                ).items()
                if key != "id"
            },
        },
        "hypothesis": {
            "claim": HYPOTHESIS,
            "falsification": "Any incomplete, nondeterministic, zero, source/open-input-mismatched, fixture-changing, conversion-changing, source-failing, or resource-failing capture rejects the oracle.",
        },
        "changedMechanism": "Attach a zero-valued marked tensor immediately before only the layer-19 FF1 matmul at the retained production block, capture its callback adjoint, and extract the initial ff1_19 BF16 payload verbatim.",
        "invariants": [
            "The production block, model, source tree, library, parameters, state, optimizer, gradients, probabilities, and update remain unchanged.",
            "The marked zero tensor changes no forward value and is consumed only as an adjoint oracle.",
            "All 64 states and 32 streams are captured in chronological state-stream order twice.",
            "The initial ff1_19 matrix is copied from the bound BF16 container payload without conversion.",
            "The captured adjoint is zero-credit teacher evidence and cannot ship in a Gamma codec.",
        ],
        "controls": [
            {"id": "marked-zero-adjoint", "role": "treatment", "definition": "Attach one marked zero tensor before the top FF1 matmul and capture its complete callback gradient."},
            {"id": "open-forward-input", "role": "comparator", "definition": "Require the independently generated open FF1 input to match the source forward operand exactly."},
            {"id": "unchanged-fixture", "role": "shifted", "definition": "Require every non-probe production fixture payload to retain its bound digest."},
            {"id": "live-adjoint", "role": "negative", "definition": "Reject an all-zero captured adjoint."},
            {"id": "independent-replay", "role": "replay", "definition": "Repeat the complete source capture and compare both input and adjoint byte-for-byte."},
        ],
        "population": {
            "unit": "BF16 top-FF1 input-adjoint words",
            "scopeBytes": 4194304,
            "scopeSymbols": 2097152,
            "selection": "Every one of 1,024 features for all 64 chronological states and 32 streams at production block 256.",
            "coordinate": "state-major, stream-major, feature-major",
        },
        "causalBoundary": {
            "availableInformation": [
                "The bound production graph and update callback.",
                "The exact open FF1 forward input for independent identity validation.",
                "The bound initial parameter container for verbatim matrix extraction.",
            ],
            "forbiddenInformation": [
                "The captured adjoint during any future open-kernel implementation or tuning.",
                "Any hidden trace, source oracle, or retained tensor in a submitted codec."
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
            predicate("k-input", "sourceInputMismatchCount", "gt", 0),
        ],
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/source-ff1-input.bf16",
            f"results/{CANDIDATE_ID}/source-ff1-input-adjoint.bf16",
            f"results/{CANDIDATE_ID}/source-initial-ff1-19.bf16",
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
