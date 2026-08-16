#!/usr/bin/env python3
"""Freeze exact open layer-19 attention forward inputs."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_top_w_o_input_adjoint_64_q0_v1_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_attention_forward_inputs_64_q0_v1"
PARENT_ID = "nncp_open_concat_head_identity_64_q0_v1"
PARENT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T175422Z_91aae07812.json"
)
SOURCE = ROOT / "results/nncp_libnc_top_attention_product_oracle_64_q0_retry_v2"
SOURCE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T174722Z_8b88b4a53d.json"
)
FORWARD = ROOT / "results/nncp_open_profile_output_bias_gradient_64_q0_retry_v1"
FORWARD_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T033450Z_727c49438a.json"
)
FIXTURE = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
FIXTURE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260815T235124Z_86c7e4f805.json"
)
OPEN_SOURCE = ROOT / (
    "results/nncp_ggml_postupdate_forward_parity_64_q1_retry_v2/"
    "ggml_profile_forward_source_closure.tar.xz"
)
PARENT_FORWARD = ROOT / (
    "programs/nncp_ggml_postupdate_forward_parity_64_q1_retry_v1/"
    "profile_forward_parity.cpp"
)
PROGRAM = ROOT / "programs" / CANDIDATE_ID
FORWARD_MATERIALIZER = PROGRAM / "materialize_forward.py"
CMAKE = PROGRAM / "CMakeLists.txt"
DESCRIPTOR = PROGRAM / "program.py"
RUNNER = ROOT / "tools/nncp_open_top_attention_forward_inputs_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
SOURCE_CEILING = 2_000_000
HYPOTHESIS = (
    "The independently exact static open forward exposes a layer-19 "
    "attention-probability population that matches all 5,242,880 source BF16 "
    "words, retains exact attended output and layer checkpoints, and produces "
    "a deterministic live value-state population sufficient for the next "
    "LibNC-free value-attention transpose."
)


def source_identifier(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    suffix = hashlib.sha256(relative.encode()).hexdigest()[:12]
    return f"runtime-source-{path.stem}-{suffix}"


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    parent_revision = ROOT / json.loads(PARENT.joinpath("decision.json").read_text())[
        "candidateRevision"
    ]["receipt"]["path"]
    inputs = [
        base.reference(PARENT / "decision.json", "parent-decision"),
        base.reference(PARENT / "execution.json", "parent-execution"),
        base.reference(PARENT / "guard.json", "parent-guard"),
        base.reference(PARENT_REFLECTION, "parent-reflection"),
        base.reference(SOURCE / "decision.json", "source-decision"),
        base.reference(SOURCE / "execution.json", "source-execution"),
        base.reference(SOURCE / "guard.json", "source-guard"),
        base.reference(SOURCE_REFLECTION, "source-reflection"),
        base.reference(
            SOURCE / "source-attention-probability-input.bf16",
            "source-probability-input",
        ),
        base.reference(
            SOURCE / "source-attended-heads-input.bf16",
            "source-attended-input",
        ),
        base.reference(FORWARD / "decision.json", "forward-decision"),
        base.reference(FORWARD / "execution.json", "forward-execution"),
        base.reference(FORWARD / "guard.json", "forward-guard"),
        base.reference(FORWARD_REFLECTION, "forward-reflection"),
        base.reference(FIXTURE / "decision.json", "fixture-decision"),
        base.reference(FIXTURE / "fixture-manifest.json", "fixture-manifest"),
        base.reference(FIXTURE / "guard.json", "fixture-guard"),
        base.reference(FIXTURE_REFLECTION, "fixture-reflection"),
        base.reference(
            FIXTURE / "fixture/parameters_initial.coefs", "initial-parameters"
        ),
        base.reference(FIXTURE / "fixture/state_initial.params", "initial-state"),
        base.reference(OPEN_SOURCE, "exact-forward-source"),
        base.reference(PARENT_FORWARD, "promoted-forward-source"),
        base.reference(FORWARD_MATERIALIZER, "forward-materializer"),
        base.reference(CMAKE, "cmake"),
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
        base.measurement("antecedentsPass", "boolean", "The exact source oracle, concat identity, open-forward parent, and initial fixture remain hash-bound."),
        base.measurement("streamCount", "streams", "Complete production stream population."),
        base.measurement("sampleCount", "state-stream samples", "Complete chronological population."),
        base.measurement("layerInputCheckpointCount", "stream-layer checkpoints", "Exact open attention-input checkpoints per replay."),
        base.measurement("layerInputMismatchCount", "BF16 elements", "Checkpoint mismatches across both replays."),
        base.measurement("maximumLayerInputAbsoluteError", "float32 value", "Maximum checkpoint error."),
        base.measurement("probabilityElementCount", "BF16 elements", "Complete layer-19 attention probability population."),
        base.measurement("valueStateElementCount", "BF16 elements", "Complete layer-19 per-stream value state."),
        base.measurement("probabilitySourceMismatchCount", "BF16 elements", "Open probability words differing from the independent source oracle."),
        base.measurement("maximumProbabilityAbsoluteError", "float32 value", "Maximum open/source probability error."),
        base.measurement("attendedSourceMismatchCount", "BF16 elements", "Open attended words differing from the independent source oracle."),
        base.measurement("maximumAttendedAbsoluteError", "float32 value", "Maximum open/source attended error."),
        base.measurement("streamMajorControlMismatchCount", "BF16 elements", "Incorrect stream/head-major probability assembly mismatches."),
        base.measurement("valueStateLive", "boolean", "The retained open value state is not all zero."),
        base.measurement("openForwardReplayIdentical", "boolean", "Two complete 32-stream populations reproduce byte-for-byte."),
        base.measurement("staticGgmlSourceBound", "boolean", "The pinned static GGML source remains explicit."),
        base.measurement("forbiddenDynamicDependencyCount", "libraries", "Dynamic LibNC, CUDA, OpenMP, or BLAS dependencies."),
        base.measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed source."),
        base.measurement("guardedWorkRootPass", "boolean", "Transient builds, fixtures, and populations were removed."),
    ]
    promotion = [
        base.predicate("p-antecedents", "antecedentsPass", "eq", True),
        base.predicate("p-streams", "streamCount", "eq", 32),
        base.predicate("p-samples", "sampleCount", "eq", 2048),
        base.predicate("p-checkpoints", "layerInputCheckpointCount", "eq", 640),
        base.predicate("p-layer", "layerInputMismatchCount", "eq", 0),
        base.predicate("p-layer-maximum", "maximumLayerInputAbsoluteError", "eq", 0.0),
        base.predicate("p-probability-elements", "probabilityElementCount", "eq", 5242880),
        base.predicate("p-value-elements", "valueStateElementCount", "eq", 10485760),
        base.predicate("p-probability", "probabilitySourceMismatchCount", "eq", 0),
        base.predicate("p-probability-maximum", "maximumProbabilityAbsoluteError", "eq", 0.0),
        base.predicate("p-attended", "attendedSourceMismatchCount", "eq", 0),
        base.predicate("p-attended-maximum", "maximumAttendedAbsoluteError", "eq", 0.0),
        base.predicate("p-control", "streamMajorControlMismatchCount", "gt", 0),
        base.predicate("p-value-live", "valueStateLive", "eq", True),
        base.predicate("p-replay", "openForwardReplayIdentical", "eq", True),
        base.predicate("p-static", "staticGgmlSourceBound", "eq", True),
        base.predicate("p-dependencies", "forbiddenDynamicDependencyCount", "eq", 0),
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
            "falsification": "Any probability or attended mismatch, stale checkpoint, incomplete population, dead value state or control, replay drift, undeclared dependency, source failure, or resource failure rejects the forward inputs.",
        },
        "changedMechanism": "Expose the already-computed layer-19 attention probability and value state from the independently exact static open forward, retain its pre-w_o output, and assemble every production stream into source-coordinate populations.",
        "invariants": [
            "The promoted open forward arithmetic and pinned static GGML source are unchanged; only existing intermediates are emitted.",
            "Every stream and state is evaluated from the sealed initial parameter and state containers twice.",
            "The source probability and attended tensors are used only as independent comparators.",
            "The value state is retained only as a zero-credit input to the next open arithmetic experiment.",
            "No teacher executable or captured tensor may ship in a Gamma codec.",
        ],
        "controls": [
            {"id": "source-order-probability", "role": "treatment", "definition": "Assemble probability as state, stream, head, key and compare every source word."},
            {"id": "attended-identity", "role": "comparator", "definition": "Recheck the same open run's attended output against the source oracle."},
            {"id": "stream-major-probability", "role": "negative", "definition": "Retain raw stream/head/state/key order and require mismatches."},
            {"id": "layer-inputs", "role": "shifted", "definition": "Recheck all open layer-input checkpoints against retained state."},
            {"id": "full-replay", "role": "replay", "definition": "Repeat all streams, outputs, assemblies, and checkpoint comparisons byte-for-byte."},
        ],
        "population": {
            "unit": "BF16 layer-19 attention probability words",
            "scopeBytes": 10485760,
            "scopeSymbols": 5242880,
            "selection": "Every key for 64 states, 32 streams, and eight heads.",
            "coordinate": "state-major, stream-major, head-major, key-major",
        },
        "causalBoundary": {
            "availableInformation": [
                "The sealed initial fixture, pinned exact-open-forward source, exact source probability/attended comparators, and frozen assembly rules."
            ],
            "forbiddenInformation": [
                "LibNC execution, tolerance, fitting to mismatches, editing source comparators, changing open arithmetic, or using future experiments.",
                "Claiming value-attention backward, a compact predictor, compression gain, or Hutter credit."
            ],
        },
        "budget": {
            "expectedGrossSavingsBytes": 0,
            "maximumAddedPackageBytes": SOURCE_CEILING,
            "expectedNetSavingsBytes": -SOURCE_CEILING,
        },
        "search": {
            "expectedTransferRetention": 1.0,
            "expectedRuntimeRatio": 1.0,
            "expectedMemoryRatio": 1.0,
            "uncertaintyRisk": 0.08,
            "interactionRisk": 0.05,
        },
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            base.predicate("k-antecedents", "antecedentsPass", "eq", True),
            base.predicate("k-probability", "probabilitySourceMismatchCount", "gt", 0),
        ],
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/open-exact-attention-probability.bf16",
            f"results/{CANDIDATE_ID}/open-exact-value-state.bf16",
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
