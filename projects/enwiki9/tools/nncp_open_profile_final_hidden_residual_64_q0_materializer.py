#!/usr/bin/env python3
"""Freeze the production open final-hidden residual projection gate."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_final_hidden_residual_64_q0_v1"
PARENT_ID = "nncp_open_profile_output_matrix_gradient_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_open_profile_final_hidden_residual_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
TAIL_DECISION = ROOT / (
    "results/nncp_open_profile_output_bias_gradient_64_q0_retry_v1/decision.json"
)
TAIL_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T033450Z_727c49438a.json"
)
MATRIX_DECISION = ROOT / f"results/{PARENT_ID}/decision.json"
MATRIX_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T040455Z_f7722f8e27.json"
)
FORWARD_ID = "nncp_ggml_postupdate_forward_parity_64_q1_retry_v2"
Q3_ID = "nncp_libnc_profile_update_fixture_64_q3_v1"


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


def source_identifier(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    digest = hashlib.sha256(relative.encode()).hexdigest()[:12]
    return f"runtime-source-{path.stem}-{digest}"


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


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    revisions = sorted(
        (ROOT / "operations/adaptive/candidate-revisions" / PARENT_ID).glob("*.json")
    )
    if not revisions:
        raise ValueError("output-matrix parent has no frozen revision")
    parent_revision = revisions[-1]
    inputs = [
        reference(
            ROOT / f"results/{FORWARD_ID}/decision.json",
            "exact-forward-decision",
        ),
        reference(
            ROOT
            / "operations/adaptive/reflections/20260816T021607Z_81c2c9ae94.json",
            "exact-forward-reflection",
        ),
        reference(
            ROOT
            / "results/nncp_open_profile_update_forward_chain_64_q0_retry_v1/decision.json",
            "joint-transition-decision",
        ),
        reference(
            ROOT
            / "operations/adaptive/reflections/20260816T024338Z_3839f396a6.json",
            "joint-transition-reflection",
        ),
        reference(ROOT / f"results/{Q3_ID}/decision.json", "gradient-oracle-decision"),
        reference(
            ROOT / f"results/{Q3_ID}/fixture-manifest.json",
            "gradient-oracle-manifest",
        ),
        reference(ROOT / f"results/{Q3_ID}/guard.json", "gradient-oracle-guard"),
        reference(
            ROOT
            / "operations/adaptive/reflections/20260815T235124Z_86c7e4f805.json",
            "gradient-oracle-reflection",
        ),
        reference(
            ROOT / "results/nncp_ggml_output_head_update_parity_qm2_v1/decision.json",
            "miniature-output-head-decision",
        ),
        reference(
            ROOT / f"results/{FORWARD_ID}/ggml_profile_forward_source_closure.tar.xz",
            "exact-forward-source",
        ),
        reference(TAIL_DECISION, "output-bias-tail-decision"),
        reference(TAIL_REFLECTION, "output-bias-tail-reflection"),
        reference(MATRIX_DECISION, "output-matrix-tail-decision"),
        reference(MATRIX_REFLECTION, "output-matrix-tail-reflection"),
        reference(RUNNER, "runner"),
        reference(MATERIALIZER, "materializer"),
    ]
    present = {value["path"] for value in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present:
            inputs.append(reference(path, source_identifier(path)))
            present.add(relative)
    measurements = [
        measurement("antecedentsPass", "boolean", "Every exact forward, open transition, complete gradient fixture, and open output-head parameter-gradient antecedent remains valid and digest-bound."),
        measurement("streamCount", "streams", "Complete production streams evaluated from retained causal input and memory state."),
        measurement("sampleCount", "symbols", "Production loss samples evaluated across all streams and states."),
        measurement("layerInputCheckpointCount", "stream-layer tensors", "Open attention-input tensors compared against retained train_h state."),
        measurement("layerInputMismatchCount", "float32 elements", "Open layer-input elements that differ from retained BF16 train_h values."),
        measurement("maximumLayerInputAbsoluteError", "float32 value", "Maximum absolute open-versus-retained layer-input difference."),
        measurement("outputBiasElementCount", "gradient elements", "Complete production output-bias gradient population retained as a tail control."),
        measurement("outputBiasMismatchCount", "gradient elements", "Open BF16 output-bias words that differ from the retained comparator."),
        measurement("maximumOutputBiasAbsoluteError", "float32 value", "Maximum absolute open-versus-retained output-bias difference."),
        measurement("outputMatrixElementCount", "gradient elements", "Complete production embed_out gradient population."),
        measurement("outputMatrixMismatchCount", "gradient elements", "Open BF16 embed_out words that differ from the retained comparator."),
        measurement("maximumOutputMatrixAbsoluteError", "float32 value", "Maximum absolute open-versus-retained embed_out difference."),
        measurement("finalHiddenResidualElementCount", "gradient elements", "Complete freshly generated BF16 final-hidden activation-residual population."),
        measurement("finalNormBiasElementCount", "gradient elements", "Complete production final-normalization bias-gradient projection."),
        measurement("finalNormBiasMismatchCount", "gradient elements", "Open BF16 final-normalization bias-gradient words that differ from the retained comparator."),
        measurement("maximumFinalNormBiasAbsoluteError", "float32 value", "Maximum absolute open-versus-retained final-normalization bias-gradient difference."),
        measurement("openGradientDeterministic", "boolean", "Two complete all-stream executions emit byte-identical output-head gradients, hidden residuals, final-normalization bias projections, controls, and checkpoint summaries."),
        measurement("shiftedTargetControlDiffers", "boolean", "A cyclic target remap changes the open final-normalization bias-gradient projection."),
        measurement("forbiddenDynamicDependencyCount", "dependencies", "Dynamic LibNC, NNCP, GGML, CUDA, OpenMP, or BLAS dependencies in built open executables."),
        measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed orchestration and open-gradient source package."),
        measurement("guardedWorkRootPass", "boolean", "Generated builds and forward outputs remained under and were removed with the guarded work root."),
    ]
    expected = {
        "antecedentsPass": True,
        "streamCount": 32,
        "sampleCount": 2048,
        "layerInputCheckpointCount": 640,
        "layerInputMismatchCount": 0,
        "maximumLayerInputAbsoluteError": 0,
        "outputBiasElementCount": 16392,
        "outputBiasMismatchCount": 0,
        "maximumOutputBiasAbsoluteError": 0,
        "outputMatrixElementCount": 16785408,
        "outputMatrixMismatchCount": 0,
        "maximumOutputMatrixAbsoluteError": 0,
        "finalHiddenResidualElementCount": 2097152,
        "finalNormBiasElementCount": 1024,
        "finalNormBiasMismatchCount": 0,
        "maximumFinalNormBiasAbsoluteError": 0,
        "openGradientDeterministic": True,
        "shiftedTargetControlDiffers": True,
        "forbiddenDynamicDependencyCount": 0,
        "guardedWorkRootPass": True,
    }
    promotion = [
        predicate(f"p-{name.lower()}", name, "eq", threshold)
        for name, threshold in expected.items()
    ]
    promotion.append(
        predicate("p-incrementalsourcebytes", "incrementalSourceBytes", "lte", 2_000_000)
    )
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
                "path": parent_revision.relative_to(ROOT).as_posix(),
                "sha256": f"sha256:{sha256(parent_revision)}",
            },
        },
        "hypothesis": {
            "claim": "The exact open BF16 loss residual propagated through the initial embed_out transpose produces a deterministic BF16 final-hidden activation residual whose broadcast reduction reproduces every retained ln_b_40 gradient word while preserving both exact output-head parameter gradients and a live shifted-target control.",
            "falsification": "Any antecedent drift, all-stream forward mismatch, output-head parameter-gradient mismatch, final-normalization bias-gradient mismatch, replay difference, dead target control, dependency violation, source overflow, or guard failure prevents promotion and forbids a final-hidden residual projection claim.",
        },
        "changedMechanism": "Multiply each exact open BF16 loss residual by the digest-bound initial embed_out transpose with the frozen 128-symbol chunked FMA order, round the complete final-hidden activation residual to BF16, and reduce it through the broadcast final-normalization bias boundary.",
        "invariants": [
            "Production geometry, initial parameters and state, targets, exact forward arithmetic, per-sample BF16 residual boundary, and both output-head parameter-gradient reductions remain unchanged.",
            "Both complete open final-hidden residuals and their final-normalization bias projections are generated before any retained gradient comparator is read.",
            "The retained output-bias and output-matrix gradient tails must remain exact in the same replay.",
            "No teacher probability, activation, or gradient payload may calculate an open residual or projection.",
            "The closed teacher, LibNC, and NNCP are not executed during retained replay.",
            "This experiment proves at most a deterministic final-hidden activation residual with an exact final-normalization bias-gradient projection; it proves no per-sample activation-residual oracle identity, normalization-input residual, transformer-layer, recursive-training, compression, transfer, package, or Hutter claim.",
        ],
        "controls": [
            {
                "id": "exact-open-all-stream-forward",
                "role": "treatment",
                "definition": "The unchanged exact forward emits final hidden states and probabilities for every retained production stream before the open output-head backward and activation-residual projection.",
            },
            {
                "id": "exact-output-head-parameter-tail",
                "role": "comparator",
                "definition": "The already promoted output-bias and output-matrix gradients remain exact in each activation-residual replay.",
            },
            {
                "id": "retained-final-norm-bias-gradient",
                "role": "comparator",
                "definition": "The captured BF16 ln_b_40 gradient is read only after both complete fresh final-hidden residual projections exist.",
            },
            {
                "id": "independent-open-replay",
                "role": "replay",
                "definition": "The complete 32-stream forward, output-head backward, final-hidden residual, and normalization-bias projection execute twice and must reproduce identical bytes.",
            },
            {
                "id": "cyclic-vocabulary-target-shift",
                "role": "negative",
                "definition": "Cyclic successor targets must change the final-normalization bias-gradient projection while probabilities, hidden states, and initial output weights remain fixed.",
            },
        ],
        "population": {
            "unit": "one production stream-layer checkpoint, BF16 parameter-gradient word, activation-residual word, or projection word",
            "scopeBytes": None,
            "scopeSymbols": 2048,
            "selection": "All 32 streams, all 64 states, all 20 layer attention inputs, all output-head parameter-gradient words, all 2,097,152 final-hidden activation-residual words, and all 1,024 ln_b_40 projection words at the first retained production update.",
            "coordinate": "Production update over original transformed-symbol coordinates [256,320) independently within each of 32 contiguous streams.",
        },
        "causalBoundary": {
            "availableInformation": [
                "Digest-bound initial parameters and memory, decoder-visible inputs and targets, exact open final hidden states and probabilities, fixed source, and frozen predicates.",
                "Retained train_h, out_bias, embed_out, and ln_b_40 gradients only after both corresponding open payloads are complete.",
            ],
            "forbiddenInformation": [
                "Teacher probabilities, teacher activations as calculation inputs, captured gradient values, post-update parameters, future symbols, fitted corrections, or LibNC/NNCP execution.",
                "Claiming per-sample activation-residual oracle identity, a normalization-input residual, broader backward, recursive training, archive, transfer, package, or objective result.",
            ],
        },
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/open-out-bias-gradient.bf16",
            f"results/{CANDIDATE_ID}/open-embed-out-gradient.bf16",
            f"results/{CANDIDATE_ID}/open-final-hidden-residual.bf16",
            f"results/{CANDIDATE_ID}/open-final-norm-bias-gradient.bf16",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
        ],
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            predicate("k-antecedents", "antecedentsPass", "eq", True),
            predicate("k-layer-input-mismatch", "layerInputMismatchCount", "gt", 0),
            predicate("k-output-bias-mismatch", "outputBiasMismatchCount", "gt", 0),
            predicate("k-output-matrix-mismatch", "outputMatrixMismatchCount", "gt", 0),
            predicate("k-final-norm-bias-mismatch", "finalNormBiasMismatchCount", "gt", 0),
        ],
        "outputManifestPolicy": "complete-result-artifacts-v1",
        "pythonSourceClosureEntries": ["runner", "materializer"],
        "budget": {
            "expectedGrossSavingsBytes": 0,
            "maximumAddedPackageBytes": 2_000_000,
            "expectedNetSavingsBytes": -2_000_000,
        },
        "search": {
            "expectedTransferRetention": 1.0,
            "expectedRuntimeRatio": 1.0,
            "expectedMemoryRatio": 1.0,
            "interactionRisk": 0.3,
            "uncertaintyRisk": 0.4,
        },
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
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
