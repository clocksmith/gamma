#!/usr/bin/env python3
"""Freeze the exact open layer-19 pre-w_o forward gate."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_w_o_input_forward_64_q0_v1"
PARENT_ID = "nncp_open_w_o_input_adjoint_block128_64_q0_v1"
PARENT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T164348Z_ff5718724e.json"
)
FORWARD = ROOT / "results/nncp_open_profile_output_bias_gradient_64_q0_retry_v1"
FORWARD_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T033450Z_727c49438a.json"
)
SOURCE = ROOT / "results/nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1"
SOURCE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T162351Z_97a6519638.json"
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
RUNNER = ROOT / "tools/nncp_open_top_w_o_input_forward_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
SOURCE_CEILING = 2_000_000
HYPOTHESIS = (
    "The independently exact open 32-stream forward, with only its layer-19 "
    "merged-attention value exposed, reproduces every one of the 2,097,152 "
    "source pre-w_o BF16 words in state-major, stream-major, feature-major "
    "order, while a stream-major assembly control differs."
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
        (PARENT / "decision.json").read_text()
    )["candidateRevision"]["receipt"]["path"]
    inputs = [
        reference(PARENT / "decision.json", "parent-decision"),
        reference(PARENT / "execution.json", "parent-execution"),
        reference(PARENT / "guard.json", "parent-guard"),
        reference(PARENT_REFLECTION, "parent-reflection"),
        reference(FORWARD / "decision.json", "forward-decision"),
        reference(FORWARD / "execution.json", "forward-execution"),
        reference(FORWARD / "guard.json", "forward-guard"),
        reference(FORWARD_REFLECTION, "forward-reflection"),
        reference(SOURCE / "decision.json", "source-decision"),
        reference(SOURCE / "execution.json", "source-execution"),
        reference(SOURCE_REFLECTION, "source-reflection"),
        reference(SOURCE / "source-w-o-input.bf16", "source-w-o-input"),
        reference(FIXTURE / "decision.json", "fixture-decision"),
        reference(FIXTURE / "fixture-manifest.json", "fixture-manifest"),
        reference(FIXTURE / "guard.json", "fixture-guard"),
        reference(FIXTURE_REFLECTION, "fixture-reflection"),
        reference(FIXTURE / "fixture/parameters_initial.coefs", "initial-parameters"),
        reference(FIXTURE / "fixture/state_initial.params", "initial-state"),
        reference(OPEN_SOURCE, "exact-forward-source"),
        reference(PARENT_FORWARD, "promoted-forward-source"),
        reference(FORWARD_MATERIALIZER, "forward-materializer"),
        reference(CMAKE, "cmake"),
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
        measurement("antecedentsPass", "boolean", "The exact source oracle, open-forward parent, update fixture, and backward transpose remain hash-bound."),
        measurement("streamCount", "streams", "Complete production training stream population."),
        measurement("sampleCount", "state-stream samples", "Complete 64-state by 32-stream population."),
        measurement("layerInputCheckpointCount", "stream-layer checkpoints", "Open attention-input checkpoints independently compared to retained train_h state."),
        measurement("layerInputMismatchCount", "BF16 elements", "Checkpoint words differing across both replays."),
        measurement("maximumLayerInputAbsoluteError", "float32 value", "Maximum open checkpoint error."),
        measurement("preWOElementCount", "BF16 elements", "Complete layer-19 merged-attention value population."),
        measurement("treatmentSourceMismatchCount", "BF16 elements", "Open state-major treatment words differing from the source oracle."),
        measurement("maximumTreatmentAbsoluteError", "float32 value", "Maximum treatment/oracle error."),
        measurement("streamMajorControlMismatchCount", "BF16 elements", "Incorrect stream-major assembly words differing from the source oracle."),
        measurement("openForwardReplayIdentical", "boolean", "Two complete 32-stream populations are byte-identical."),
        measurement("staticGgmlSourceBound", "boolean", "The pinned static GGML CPU source dependency remains explicit."),
        measurement("forbiddenDynamicDependencyCount", "libraries", "Dynamic dependencies on LibNC, CUDA, OpenMP, or BLAS."),
        measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed incremental source."),
        measurement("guardedWorkRootPass", "boolean", "Transient work was removed."),
    ]
    promotion = [
        predicate("p-antecedents", "antecedentsPass", "eq", True),
        predicate("p-streams", "streamCount", "eq", 32),
        predicate("p-samples", "sampleCount", "eq", 2048),
        predicate("p-checkpoints", "layerInputCheckpointCount", "eq", 640),
        predicate("p-layer-identity", "layerInputMismatchCount", "eq", 0),
        predicate("p-layer-maximum", "maximumLayerInputAbsoluteError", "eq", 0.0),
        predicate("p-elements", "preWOElementCount", "eq", 2097152),
        predicate("p-treatment", "treatmentSourceMismatchCount", "eq", 0),
        predicate("p-maximum", "maximumTreatmentAbsoluteError", "eq", 0.0),
        predicate("p-control", "streamMajorControlMismatchCount", "gt", 0),
        predicate("p-replay", "openForwardReplayIdentical", "eq", True),
        predicate("p-static-source", "staticGgmlSourceBound", "eq", True),
        predicate("p-dynamic-dependencies", "forbiddenDynamicDependencyCount", "eq", 0),
        predicate("p-source", "incrementalSourceBytes", "lte", SOURCE_CEILING),
        predicate("p-work", "guardedWorkRootPass", "eq", True),
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
                for key, value in reference(parent_revision, "parent-revision").items()
                if key != "id"
            },
        },
        "hypothesis": {
            "claim": HYPOTHESIS,
            "falsification": "Any treatment mismatch, stale layer checkpoint, dead coordinate control, nondeterministic replay, undeclared dependency, or resource failure rejects the open forward boundary.",
        },
        "changedMechanism": "Expose the already-computed layer-19 merged-attention value from the independently exact open forward and assemble the complete production population in the source tensor coordinate order.",
        "invariants": [
            "The promoted open forward arithmetic and pinned static GGML source are unchanged; only one existing intermediate is emitted.",
            "Every stream and state is evaluated from the sealed initial parameter and state containers.",
            "The source pre-w_o tensor is used only as an independently captured comparator.",
            "The source tensor, fixture, and GGML dependency are zero-credit evidence and cannot be omitted from final package accounting.",
        ],
        "controls": [
            {"id": "state-major", "role": "treatment", "definition": "Assemble per-stream outputs in state-major, stream-major, feature-major source order."},
            {"id": "stream-major", "role": "comparator", "definition": "Assemble the same computed values in incorrect stream-major, state-major, feature-major order."},
            {"id": "replay", "role": "replay", "definition": "Repeat all 32 open-forward streams and both assemblies byte-for-byte."},
        ],
        "population": {
            "unit": "BF16 layer-19 pre-w_o words",
            "scopeBytes": 4194304,
            "scopeSymbols": 2097152,
            "selection": "Every feature for all 64 states and all 32 production streams.",
            "coordinate": "state-major, stream-major, feature-major",
        },
        "causalBoundary": {
            "availableInformation": [
                "The prospectively sealed initial fixture, pinned exact-open-forward source, and independent source comparator.",
                "The output exposure and tensor-coordinate assembly are frozen before execution.",
            ],
            "forbiddenInformation": [
                "LibNC execution, fitting to mismatches, tolerance, editing the source comparator, or changing open-forward arithmetic.",
                "Claiming a compact dependency-free predictor, an open attention backward path, compression gain, or Hutter credit.",
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
            "uncertaintyRisk": 0.1,
            "interactionRisk": 0.1,
        },
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            predicate("k-antecedents", "antecedentsPass", "eq", True),
            predicate("k-treatment", "treatmentSourceMismatchCount", "gt", 0),
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
