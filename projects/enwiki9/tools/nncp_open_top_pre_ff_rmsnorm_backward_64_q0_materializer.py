#!/usr/bin/env python3
"""Freeze the open layer-19 pre-FF RMSNorm backward experiment."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_ff1_weight_slice_schedule_64_q0 as forward_parent
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_pre_ff_rmsnorm_backward_64_q0_v1"
PARENT_ID = "nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_open_top_pre_ff_rmsnorm_backward_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
DESCRIPTOR = PROGRAM / "program.py"
FORWARD_MATERIALIZER = PROGRAM / "materialize_pre_ff_forward.py"
BACKWARD_MATERIALIZER = PROGRAM / "materialize_pre_ff_backward.py"
CMAKE = PROGRAM / "CMakeLists.txt"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T130603Z_423b21f22f.json"
)
FF1_RESULT = ROOT / "results/nncp_open_top_ff1_input_adjoint_block128_64_q0_v1"
FF1_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T123635Z_f1f6615808.json"
)
NORMALIZED_INPUT = ROOT / (
    "results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1/"
    "open-ff1-input.bf16"
)
NORMALIZED_ADJOINT = FF1_RESULT / "source-exact-ff1-input-adjoint.bf16"
FINAL_RESULT = ROOT / (
    "results/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2"
)
FINAL_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T082228Z_f0bff9b6df.json"
)
FINAL_BACKWARD = ROOT / (
    "programs/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2/"
    "final_norm_backward.cpp"
)
DIRECT_ADJOINT = ROOT / (
    "results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/"
    "open-final-hidden-residual.bf16"
)
FIXTURE = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
GAIN = FIXTURE / "fixture/gradients/0003_ln_g_39.bin"
GAIN_META = FIXTURE / "fixture/gradients/0003_ln_g_39.meta"
BIAS = FIXTURE / "fixture/gradients/0004_ln_b_39.bin"
BIAS_META = FIXTURE / "fixture/gradients/0004_ln_b_39.meta"
PARENT_FORWARD_MATERIALIZER = ROOT / (
    "programs/nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v2/"
    "materialize_forward.py"
)
FF1_INPUT_MATERIALIZER = ROOT / (
    "programs/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1/"
    "materialize_ff1_input.py"
)
OPEN_SOURCE = forward_parent.profile.base.parent.OPEN_SOURCE
SOURCE_CEILING = 2_000_000
HYPOTHESIS = (
    "The exact final-RMSNorm arithmetic contract transfers unchanged to layer "
    "19: open forward hidden state, normalized FF adjoint, ln_g_39, and the "
    "direct residual reproduce both retained affine gradients and every source "
    "total hidden-adjoint word."
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
        reference(
            PARENT_RESULT / "source-pre-ff-hidden.bf16",
            "source-pre-ff-hidden",
        ),
        reference(
            PARENT_RESULT / "source-pre-ff-hidden-adjoint.bf16",
            "source-pre-ff-hidden-adjoint",
        ),
        reference(FF1_RESULT / "decision.json", "ff1-decision"),
        reference(FF1_RESULT / "execution.json", "ff1-execution"),
        reference(FF1_RESULT / "guard.json", "ff1-guard"),
        reference(FF1_REFLECTION, "ff1-reflection"),
        reference(NORMALIZED_INPUT, "normalized-ff1-input"),
        reference(NORMALIZED_ADJOINT, "normalized-ff1-input-adjoint"),
        reference(FINAL_RESULT / "decision.json", "final-decision"),
        reference(FINAL_RESULT / "execution.json", "final-execution"),
        reference(FINAL_RESULT / "guard.json", "final-guard"),
        reference(FINAL_REFLECTION, "final-reflection"),
        reference(FINAL_BACKWARD, "exact-final-backward-source"),
        reference(DIRECT_ADJOINT, "direct-residual-adjoint"),
        reference(FIXTURE / "decision.json", "fixture-decision"),
        reference(FIXTURE / "fixture-manifest.json", "fixture-manifest"),
        reference(
            FIXTURE / "fixture/parameters_initial.coefs", "initial-parameters"
        ),
        reference(GAIN, "retained-ln-g-39-gradient"),
        reference(GAIN_META, "retained-ln-g-39-meta"),
        reference(BIAS, "retained-ln-b-39-gradient"),
        reference(BIAS_META, "retained-ln-b-39-meta"),
        reference(OPEN_SOURCE, "open-forward-source-archive"),
        reference(
            PARENT_FORWARD_MATERIALIZER, "parent-forward-materializer"
        ),
        reference(FF1_INPUT_MATERIALIZER, "ff1-input-materializer"),
        reference(FORWARD_MATERIALIZER, "pre-ff-forward-materializer"),
        reference(BACKWARD_MATERIALIZER, "pre-ff-backward-materializer"),
        reference(CMAKE, "cmake-contract"),
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
        measurement("antecedentsPass", "boolean", "The source boundary, exact FF1 adjoint, final-RMSNorm arithmetic receipt, direct residual, forward source, and retained gradients remain hash-bound."),
        measurement("sampleCount", "state-stream samples", "Complete layer-19 pre-FF population per replay."),
        measurement("layerInputCheckpointCount", "checkpoints", "Open forward layer-input checkpoints across both replays."),
        measurement("layerInputMismatchCount", "float32 values", "Open forward layer-input values differing from the retained state."),
        measurement("maximumLayerInputAbsoluteError", "float32 value", "Maximum open/retained layer-input error."),
        measurement("hiddenElementCount", "BF16 elements", "Words in the complete open pre-FF hidden population."),
        measurement("hiddenSourceMismatchCount", "BF16 elements", "Open pre-FF hidden words differing from the source probe."),
        measurement("maximumHiddenSourceAbsoluteError", "float32 value", "Maximum open/source pre-FF hidden error."),
        measurement("normalizedInputMismatchCount", "BF16 elements", "Regenerated normalized FF1 input words differing from the prior exact open operand."),
        measurement("maximumNormalizedInputAbsoluteError", "float32 value", "Maximum regenerated/prior normalized input error."),
        measurement("gainGradientElementCount", "BF16 elements", "Words in the complete ln_g_39 gradient."),
        measurement("gainGradientMismatchCount", "BF16 elements", "Open ln_g_39 gradient words differing from the retained fixture."),
        measurement("maximumGainGradientAbsoluteError", "float32 value", "Maximum open/retained ln_g_39 gradient error."),
        measurement("biasGradientElementCount", "BF16 elements", "Words in the complete ln_b_39 gradient."),
        measurement("biasGradientMismatchCount", "BF16 elements", "Open ln_b_39 gradient words differing from the retained fixture."),
        measurement("maximumBiasGradientAbsoluteError", "float32 value", "Maximum open/retained ln_b_39 gradient error."),
        measurement("totalAdjointElementCount", "BF16 elements", "Words in the complete merged pre-FF hidden adjoint."),
        measurement("totalAdjointMismatchCount", "BF16 elements", "Open merged hidden-adjoint words differing from the source oracle."),
        measurement("maximumTotalAdjointAbsoluteError", "float32 value", "Maximum open/source total-adjoint error."),
        measurement("directOnlyControlMismatchCount", "BF16 elements", "Direct-only control words differing from the source total adjoint."),
        measurement("negatedBranchControlMismatchCount", "BF16 elements", "Negated normalized-branch control words differing from the source total adjoint."),
        measurement("openReplayIdentical", "boolean", "Two complete forward and backward populations reproduce byte-for-byte."),
        measurement("forbiddenDynamicDependencyCount", "dependencies", "LibNC, GGML, BLAS, OpenMP, or CUDA dynamic dependencies in either executable."),
        measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed open source."),
        measurement("guardedWorkRootPass", "boolean", "All transient forward, build, and evaluation payloads were removed."),
    ]
    promotion = [
        predicate("p-antecedents", "antecedentsPass", "eq", True),
        predicate("p-samples", "sampleCount", "eq", 2048),
        predicate("p-checkpoints", "layerInputCheckpointCount", "eq", 1280),
        predicate("p-layer-input", "layerInputMismatchCount", "eq", 0),
        predicate("p-layer-maximum", "maximumLayerInputAbsoluteError", "eq", 0.0),
        predicate("p-hidden-elements", "hiddenElementCount", "eq", 2097152),
        predicate("p-hidden", "hiddenSourceMismatchCount", "eq", 0),
        predicate("p-hidden-maximum", "maximumHiddenSourceAbsoluteError", "eq", 0.0),
        predicate("p-normalized", "normalizedInputMismatchCount", "eq", 0),
        predicate("p-normalized-maximum", "maximumNormalizedInputAbsoluteError", "eq", 0.0),
        predicate("p-gain-elements", "gainGradientElementCount", "eq", 1024),
        predicate("p-gain", "gainGradientMismatchCount", "eq", 0),
        predicate("p-gain-maximum", "maximumGainGradientAbsoluteError", "eq", 0.0),
        predicate("p-bias-elements", "biasGradientElementCount", "eq", 1024),
        predicate("p-bias", "biasGradientMismatchCount", "eq", 0),
        predicate("p-bias-maximum", "maximumBiasGradientAbsoluteError", "eq", 0.0),
        predicate("p-total-elements", "totalAdjointElementCount", "eq", 2097152),
        predicate("p-total", "totalAdjointMismatchCount", "eq", 0),
        predicate("p-total-maximum", "maximumTotalAdjointAbsoluteError", "eq", 0.0),
        predicate("p-direct-control", "directOnlyControlMismatchCount", "gt", 0),
        predicate("p-negated-control", "negatedBranchControlMismatchCount", "gt", 0),
        predicate("p-replay", "openReplayIdentical", "eq", True),
        predicate("p-dependencies", "forbiddenDynamicDependencyCount", "eq", 0),
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
            "falsification": "Any open/source hidden mismatch, affine-gradient mismatch, total-adjoint mismatch, dead control, replay failure, forbidden dependency, source failure, or resource failure rejects the transfer.",
        },
        "changedMechanism": "Retarget the already exact final RMSNorm backward source to ln_g_39 and layer-19 pre-FF inputs, preserve its reduction and BF16 contracts, then add the exact direct residual branch with one BF16 conversion.",
        "invariants": [
            "The forward model, parameters, state, sample order, normalized FF adjoint, direct residual, retained gradients, and source comparators remain unchanged.",
            "The arithmetic implementation is digest-frozen before the new source comparator is consulted.",
            "Both complete open replays are generated before any source comparison; tolerance and coordinate repair are forbidden.",
            "Neither executable has a LibNC, GGML, BLAS, OpenMP, or CUDA dynamic dependency.",
            "The source oracle is zero-credit validation and cannot ship in a Gamma codec.",
        ],
        "controls": [
            {"id": "transferred-rmsnorm-plus-residual", "role": "treatment", "definition": "Use the exact prior final-RMSNorm backward contract with ln_g_39, then BF16-add the direct residual."},
            {"id": "source-boundary", "role": "comparator", "definition": "Compare the complete open hidden state and total adjoint only after both open populations exist."},
            {"id": "retained-affine-gradients", "role": "shifted", "definition": "Require independent exact ln_g_39 and ln_b_39 parameter-gradient parity."},
            {"id": "direct-only", "role": "negative", "definition": "Remove the normalized FF branch while preserving the direct residual."},
            {"id": "negated-normalized-branch", "role": "negative", "definition": "Negate the normalized FF branch before the same residual merge."},
            {"id": "independent-replay", "role": "replay", "definition": "Rebuild every forward sample and backward output twice."},
        ],
        "population": {
            "unit": "BF16 layer-19 pre-FF hidden-adjoint words",
            "scopeBytes": 4194304,
            "scopeSymbols": 2097152,
            "selection": "Every one of 1,024 features for all 64 chronological states and 32 streams.",
            "coordinate": "state-major, stream-major, feature-major",
        },
        "causalBoundary": {
            "availableInformation": [
                "The digest-bound exact open forward source and prior exact final-RMSNorm backward source.",
                "The exact normalized FF adjoint, direct residual, initial ln_g_39 parameter, and retained affine gradients.",
                "The source hidden and total-adjoint comparators only after complete open populations exist.",
            ],
            "forbiddenInformation": [
                "Comparator-derived constants, coordinate-specific branches, tolerance, fitted correction, LibNC/GGML dynamic execution, or source tensors in a submitted codec."
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
            "uncertaintyRisk": 0.15,
            "interactionRisk": 0.1,
        },
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            predicate("k-antecedents", "antecedentsPass", "eq", True),
            predicate("k-total", "totalAdjointMismatchCount", "gt", 0),
        ],
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/open-pre-ff-hidden.bf16",
            f"results/{CANDIDATE_ID}/open-ln-g-39-gradient.bf16",
            f"results/{CANDIDATE_ID}/open-ln-b-39-gradient.bf16",
            f"results/{CANDIDATE_ID}/open-pre-ff-norm-input-adjoint.bf16",
            f"results/{CANDIDATE_ID}/source-exact-pre-ff-total-adjoint.bf16",
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
