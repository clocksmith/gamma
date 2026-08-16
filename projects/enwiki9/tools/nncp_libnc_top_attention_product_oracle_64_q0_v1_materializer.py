#!/usr/bin/env python3
"""Freeze the production top attention-product source oracle."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_top_w_o_input_adjoint_64_q0_v1_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_attention_product_oracle_64_q0_v1"
PARENT_ID = "nncp_open_top_w_o_input_forward_64_q0_retry_v2"
PARENT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T171305Z_fdae41e74c.json"
)
BACKWARD = ROOT / "results/nncp_open_w_o_input_adjoint_block128_64_q0_v1"
BACKWARD_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T164348Z_ff5718724e.json"
)
FIXTURE = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
FIXTURE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260815T235124Z_86c7e4f805.json"
)
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RUNNER = ROOT / "tools/nncp_libnc_top_attention_product_oracle_64_q0_v1.py"
MATERIALIZER = Path(__file__).resolve()
PROBE = ROOT / "tools/nncp_libnc_top_attention_product_probe_q0.c"
DESCRIPTOR = PROGRAM / "program.py"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
SOURCE_CEILING = 2_000_000
HYPOTHESIS = (
    "Two same-run production probes at the layer-19 value-attention product "
    "and its probability operand yield deterministic, complete BF16 forward "
    "and adjoint populations, preserve every non-probe fixture payload, and "
    "the attended-head input maps exactly through concat_head to the promoted "
    "open pre-w_o value."
)


def source_identifier(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    suffix = hashlib.sha256(relative.encode()).hexdigest()[:12]
    return f"runtime-source-{path.stem}-{suffix}"


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    parent_revision = ROOT / json.loads(
        (PARENT / "decision.json").read_text()
    )["candidateRevision"]["receipt"]["path"]
    inputs = [
        base.reference(PARENT / "decision.json", "parent-decision"),
        base.reference(PARENT / "execution.json", "parent-execution"),
        base.reference(PARENT / "guard.json", "parent-guard"),
        base.reference(PARENT_REFLECTION, "parent-reflection"),
        base.reference(PARENT / "open-exact-w-o-input.bf16", "open-pre-w-o-input"),
        base.reference(BACKWARD / "decision.json", "backward-decision"),
        base.reference(BACKWARD / "execution.json", "backward-execution"),
        base.reference(BACKWARD / "guard.json", "backward-guard"),
        base.reference(BACKWARD_REFLECTION, "backward-reflection"),
        base.reference(
            BACKWARD / "source-exact-w-o-input-adjoint.bf16",
            "open-pre-w-o-adjoint",
        ),
        base.reference(FIXTURE / "decision.json", "fixture-decision"),
        base.reference(FIXTURE / "fixture-manifest.json", "fixture-manifest"),
        base.reference(FIXTURE / "guard.json", "fixture-guard"),
        base.reference(FIXTURE_REFLECTION, "fixture-reflection"),
        base.reference(PROBE, "probe-source"),
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
        base.measurement("antecedentsPass", "boolean", "The exact pre-w_o forward, backward transpose, production fixture, source tree, and probe remain hash-bound."),
        base.measurement("captureCount", "captures", "Independent complete source capture populations."),
        base.measurement("sampleCount", "state-stream samples", "Complete chronological production population."),
        base.measurement("attendedInputElementCount", "BF16 elements", "Words in the combined attended-head forward value."),
        base.measurement("attendedAdjointElementCount", "BF16 elements", "Words in the combined attended-head adjoint."),
        base.measurement("probabilityInputElementCount", "BF16 elements", "Words in the combined attention-probability forward value."),
        base.measurement("probabilityAdjointElementCount", "BF16 elements", "Words in the combined attention-probability adjoint."),
        base.measurement("sourceCaptureDeterministic", "boolean", "Both four-tensor source populations reproduce byte-for-byte."),
        base.measurement("declaredProbeFileCount", "files", "Declared top-attention bin/meta files across both captures."),
        base.measurement("declaredProbePopulationExact", "boolean", "Each capture contains exactly every frozen kind, phase, state, and extension."),
        base.measurement("fixturePayloadIdentical", "boolean", "Every non-probe production fixture payload remains unchanged."),
        base.measurement("fixturePayloadMismatchCount", "files", "Non-probe fixture mismatches across both captures."),
        base.measurement("attendedInputLive", "boolean", "The attended-head input is not all zero."),
        base.measurement("attendedAdjointLive", "boolean", "The attended-head adjoint is not all zero."),
        base.measurement("probabilityInputLive", "boolean", "The probability input is not all zero."),
        base.measurement("probabilityAdjointLive", "boolean", "The probability adjoint is not all zero."),
        base.measurement("concatSourceMismatchCount", "BF16 elements", "Source attended-head values, mapped by concat_head coordinates, differing from the exact open pre-w_o tensor."),
        base.measurement("maximumConcatAbsoluteError", "float32 value", "Maximum mapped attended/open pre-w_o error."),
        base.measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed oracle source."),
        base.measurement("guardedWorkRootPass", "boolean", "Transient builds and raw fixture trees were removed."),
    ]
    promotion = [
        base.predicate("p-antecedents", "antecedentsPass", "eq", True),
        base.predicate("p-captures", "captureCount", "eq", 2),
        base.predicate("p-samples", "sampleCount", "eq", 2048),
        base.predicate("p-attended-input-elements", "attendedInputElementCount", "eq", 2097152),
        base.predicate("p-attended-adjoint-elements", "attendedAdjointElementCount", "eq", 2097152),
        base.predicate("p-probability-input-elements", "probabilityInputElementCount", "eq", 5242880),
        base.predicate("p-probability-adjoint-elements", "probabilityAdjointElementCount", "eq", 5242880),
        base.predicate("p-deterministic", "sourceCaptureDeterministic", "eq", True),
        base.predicate("p-probe-files", "declaredProbeFileCount", "eq", 1024),
        base.predicate("p-probe-population", "declaredProbePopulationExact", "eq", True),
        base.predicate("p-fixture", "fixturePayloadIdentical", "eq", True),
        base.predicate("p-fixture-count", "fixturePayloadMismatchCount", "eq", 0),
        base.predicate("p-attended-input-live", "attendedInputLive", "eq", True),
        base.predicate("p-attended-adjoint-live", "attendedAdjointLive", "eq", True),
        base.predicate("p-probability-input-live", "probabilityInputLive", "eq", True),
        base.predicate("p-probability-adjoint-live", "probabilityAdjointLive", "eq", True),
        base.predicate("p-concat", "concatSourceMismatchCount", "eq", 0),
        base.predicate("p-concat-maximum", "maximumConcatAbsoluteError", "eq", 0.0),
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
            "falsification": "Any incomplete, nondeterministic, dead, fixture-changing, concat-mismatching, source-failing, or resource-failing capture rejects the oracle.",
        },
        "changedMechanism": "Attach zero-valued marked tensors to the layer-19 attention probability before its value matmul and to the attended-head result before concat_head at production block 256; capture their complete forward values and callback adjoints twice.",
        "invariants": [
            "The production model, block, parameters, state, optimizer, update, and every non-probe fixture payload remain unchanged.",
            "Marked zero tensors change no forward value and exist only to expose callback adjoints.",
            "All four tensors cover every state, head, stream, and feature or key coordinate twice.",
            "The attended-head source input must independently map to the promoted open pre-w_o tensor through the declared concat_head permutation.",
            "All captures remain zero-credit teacher evidence and cannot ship in a Gamma codec.",
        ],
        "controls": [
            {"id": "marked-zero-adjoints", "role": "treatment", "definition": "Attach independent marked zeros at both product boundaries and capture complete callback adjoints."},
            {"id": "concat-forward-identity", "role": "comparator", "definition": "Map the captured attended-head input through concat_head coordinates and compare every word to the promoted open pre-w_o tensor."},
            {"id": "unchanged-fixture", "role": "shifted", "definition": "Require every non-probe fixture payload to retain its bound digest."},
            {"id": "live-tensors", "role": "negative", "definition": "Reject any all-zero forward or adjoint tensor."},
            {"id": "independent-replay", "role": "replay", "definition": "Repeat the complete source capture and compare all four tensor populations byte-for-byte."},
        ],
        "population": {
            "unit": "BF16 top-attention forward and adjoint words",
            "scopeBytes": 29360128,
            "scopeSymbols": 14680064,
            "selection": "Every attended-head and probability word across 64 states, eight heads, 32 streams, and the complete feature or key axis.",
            "coordinate": "state-major, head-major, stream-major, feature-or-key-major",
        },
        "causalBoundary": {
            "availableInformation": [
                "The bound production graph/update callback and exact open pre-w_o forward/backward artifacts.",
                "Only the frozen probe namespace, concat mapping, and full-population gates are evaluated.",
            ],
            "forbiddenInformation": [
                "Using captured adjoints during future open arithmetic implementation, fitting to mismatch coordinates, or editing source comparators.",
                "Shipping teacher tensors or claiming open attention parity, compression gain, or Hutter credit from this oracle.",
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
            base.predicate("k-antecedents", "antecedentsPass", "eq", True),
            base.predicate("k-fixture", "fixturePayloadMismatchCount", "gt", 0),
            base.predicate("k-concat", "concatSourceMismatchCount", "gt", 0),
        ],
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/source-attended-heads-input.bf16",
            f"results/{CANDIDATE_ID}/source-attended-heads-adjoint.bf16",
            f"results/{CANDIDATE_ID}/source-attention-probability-input.bf16",
            f"results/{CANDIDATE_ID}/source-attention-probability-adjoint.bf16",
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
