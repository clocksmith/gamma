#!/usr/bin/env python3
"""Freeze the production open final RMSNorm backward gate."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_final_norm_backward_64_q0_v1"
PARENT_ID = "nncp_open_profile_final_hidden_residual_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_open_profile_final_norm_backward_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PARENT_EXPERIMENT = ROOT / (
    "operations/adaptive/experiments/"
    "nncp_open_profile_final_hidden_residual_64_q0_v1.json"
)
PARENT_DECISION = ROOT / "results" / PARENT_ID / "decision.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T043203Z_ca54b4761d.json"
)
PARENT_RESIDUAL = ROOT / "results" / PARENT_ID / "open-final-hidden-residual.bf16"
RMS_ORDER_DECISION = ROOT / (
    "results/nncp_v33_libnc_rmsnorm_backward_order_parity_v1/decision.json"
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
    parent_reflection = json.loads(PARENT_REFLECTION.read_text())
    parent_revision_path = ROOT / parent_reflection["candidateRevision"]["receipt"]["path"]
    parent_experiment = json.loads(PARENT_EXPERIMENT.read_text())
    inputs = [
        item
        for item in parent_experiment["inputs"]
        if item["id"] not in ("runner", "materializer")
        and not item["id"].startswith("runtime-source-")
    ]
    inputs.extend(
        (
            reference(PARENT_DECISION, "final-hidden-residual-decision"),
            reference(PARENT_REFLECTION, "final-hidden-residual-reflection"),
            reference(PARENT_RESIDUAL, "promoted-final-hidden-residual"),
            reference(RMS_ORDER_DECISION, "rmsnorm-output-order-decision"),
            reference(RUNNER, "runner"),
            reference(MATERIALIZER, "materializer"),
        )
    )
    present = {value["path"] for value in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present:
            inputs.append(reference(path, source_identifier(path)))
            present.add(relative)
    measurements = [
        measurement("antecedentsPass", "boolean", "Every exact forward, open output-head backward, promoted final-hidden residual, complete gradient fixture, and measured RMSNorm operation-order antecedent remains valid and digest-bound."),
        measurement("streamCount", "streams", "Complete production streams evaluated from retained causal input and memory state."),
        measurement("sampleCount", "symbols", "Production loss samples evaluated across all streams and states."),
        measurement("layerInputCheckpointCount", "stream-layer tensors", "Open attention-input tensors compared against retained train_h state."),
        measurement("layerInputMismatchCount", "float32 elements", "Open layer-input elements that differ from retained BF16 train_h values across both replays."),
        measurement("maximumLayerInputAbsoluteError", "float32 value", "Maximum absolute open-versus-retained layer-input difference."),
        measurement("outputBiasMismatchCount", "gradient elements", "Retained output-bias tail words that differ in the successor replay."),
        measurement("maximumOutputBiasAbsoluteError", "float32 value", "Maximum absolute output-bias tail difference."),
        measurement("outputMatrixMismatchCount", "gradient elements", "Retained embed_out tail words that differ in the successor replay."),
        measurement("maximumOutputMatrixAbsoluteError", "float32 value", "Maximum absolute embed_out tail difference."),
        measurement("promotedHiddenResidualMismatchCount", "gradient elements", "Fresh final-hidden residual words that differ from the promoted open residual artifact."),
        measurement("maximumPromotedHiddenResidualAbsoluteError", "float32 value", "Maximum absolute fresh-versus-promoted final-hidden residual difference."),
        measurement("finalNormGainElementCount", "gradient elements", "Complete production ln_g_40 gradient population."),
        measurement("finalNormGainMismatchCount", "gradient elements", "Open BF16 ln_g_40 words that differ from the retained comparator."),
        measurement("maximumFinalNormGainAbsoluteError", "float32 value", "Maximum absolute open-versus-retained ln_g_40 difference."),
        measurement("finalNormBiasElementCount", "gradient elements", "Complete production ln_b_40 gradient population."),
        measurement("finalNormBiasMismatchCount", "gradient elements", "Open BF16 ln_b_40 words that differ from the retained comparator."),
        measurement("maximumFinalNormBiasAbsoluteError", "float32 value", "Maximum absolute open-versus-retained ln_b_40 difference."),
        measurement("finalNormInputResidualElementCount", "gradient elements", "Complete freshly generated BF16 final RMSNorm input-residual population."),
        measurement("topFeedforwardBiasElementCount", "gradient elements", "Complete production ff_bias2_19 gradient projection."),
        measurement("topFeedforwardBiasMismatchCount", "gradient elements", "Open BF16 ff_bias2_19 projection words that differ from the retained comparator."),
        measurement("maximumTopFeedforwardBiasAbsoluteError", "float32 value", "Maximum absolute open-versus-retained ff_bias2_19 difference."),
        measurement("openBackwardDeterministic", "boolean", "Two complete executions emit byte-identical forwards, retained tails, normalization gradients, input residuals, projections, and controls."),
        measurement("shiftedTargetControlDiffers", "boolean", "The retained cyclic target remap still changes the final-normalization bias projection."),
        measurement("negatedResidualControlDiffers", "boolean", "Negating the independently generated incoming residual changes the top-layer feedforward-bias projection."),
        measurement("forbiddenDynamicDependencyCount", "dependencies", "Dynamic LibNC, NNCP, GGML, CUDA, OpenMP, or BLAS dependencies in built open executables."),
        measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed orchestration and open-backward source package."),
        measurement("guardedWorkRootPass", "boolean", "Generated builds and forward outputs remained under and were removed with the guarded work root."),
    ]
    expected = {
        "antecedentsPass": True,
        "streamCount": 32,
        "sampleCount": 2048,
        "layerInputCheckpointCount": 640,
        "layerInputMismatchCount": 0,
        "maximumLayerInputAbsoluteError": 0,
        "outputBiasMismatchCount": 0,
        "maximumOutputBiasAbsoluteError": 0,
        "outputMatrixMismatchCount": 0,
        "maximumOutputMatrixAbsoluteError": 0,
        "promotedHiddenResidualMismatchCount": 0,
        "maximumPromotedHiddenResidualAbsoluteError": 0,
        "finalNormGainElementCount": 1024,
        "finalNormGainMismatchCount": 0,
        "maximumFinalNormGainAbsoluteError": 0,
        "finalNormBiasElementCount": 1024,
        "finalNormBiasMismatchCount": 0,
        "maximumFinalNormBiasAbsoluteError": 0,
        "finalNormInputResidualElementCount": 2097152,
        "topFeedforwardBiasElementCount": 1024,
        "topFeedforwardBiasMismatchCount": 0,
        "maximumTopFeedforwardBiasAbsoluteError": 0,
        "openBackwardDeterministic": True,
        "shiftedTargetControlDiffers": True,
        "negatedResidualControlDiffers": True,
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
                "path": parent_revision_path.relative_to(ROOT).as_posix(),
                "sha256": f"sha256:{sha256(parent_revision_path)}",
            },
        },
        "hypothesis": {
            "claim": "The promoted final-hidden residual and exact open pre-normalization state reproduce both final RMSNorm parameter gradients and an input residual whose broadcast projection equals the retained top-layer ff_bias2_19 gradient under the measured LibNC output-order RMSNorm backward.",
            "falsification": "Any antecedent drift, replay mismatch, retained output-head-tail mismatch, promoted-residual mismatch, ln_g_40 or ln_b_40 mismatch, ff_bias2_19 projection mismatch, dead control, dependency violation, source overflow, or guard failure prevents promotion and forbids a final RMSNorm input-backward claim.",
        },
        "changedMechanism": "Expose the exact pre-final-normalization hidden state, reconstruct the final RMSNorm unit value with the promoted forward reduction, apply the measured output-order backward to the promoted incoming residual, and validate the resulting parameter gradients and input residual through separate retained projections.",
        "invariants": [
            "Production geometry, initial parameters and state, targets, exact forward arithmetic, BF16 loss-residual boundary, output-head reductions, and promoted final-hidden residual remain unchanged.",
            "Both complete final RMSNorm backward payloads are generated before any retained ln_g_40, ln_b_40, or ff_bias2_19 comparator is read.",
            "The complete output-head parameter and activation-residual tails must remain exact in the same replay.",
            "No teacher probability, teacher activation, or captured gradient may calculate an open normalization gradient or input residual.",
            "The closed teacher, LibNC, and NNCP are not executed during retained replay.",
            "This experiment proves at most the final RMSNorm parameter gradients and an input residual with an exact top-layer bias projection; it proves no transformer-block backward, recursive training, compression, transfer, package, or Hutter result.",
        ],
        "controls": [
            {
                "id": "promoted-output-head-backward",
                "role": "treatment",
                "definition": "Each fresh all-stream execution reproduces both output-head parameter gradients and the promoted final-hidden residual before the final RMSNorm backward runs.",
            },
            {
                "id": "retained-final-norm-parameters",
                "role": "comparator",
                "definition": "Captured BF16 ln_g_40 and ln_b_40 gradients are read only after both fresh normalization payloads exist.",
            },
            {
                "id": "retained-top-feedforward-bias",
                "role": "comparator",
                "definition": "Captured BF16 ff_bias2_19 is an independent broadcast projection of the final-normalization input residual and is read only after both fresh projections exist.",
            },
            {
                "id": "independent-open-replay",
                "role": "replay",
                "definition": "The complete 32-stream forward, output-head backward, final RMSNorm backward, and projection execute twice and must reproduce identical bytes.",
            },
            {
                "id": "negated-incoming-residual",
                "role": "negative",
                "definition": "A sign-inverted incoming residual must change the top-layer feedforward-bias projection while state, parameters, and normalization inputs remain fixed.",
            },
        ],
        "population": {
            "unit": "one production stream-layer checkpoint, BF16 gradient word, activation-residual word, or projection word",
            "scopeBytes": None,
            "scopeSymbols": 2048,
            "selection": "All 32 streams, all 64 states, all 20 layer attention inputs, both complete output-head gradients, all final-hidden residual words, all final RMSNorm parameter-gradient words, all 2,097,152 normalization-input residual words, and all 1,024 ff_bias2_19 projection words at the first retained production update.",
            "coordinate": "Production update over original transformed-symbol coordinates [256,320) independently within each of 32 contiguous streams.",
        },
        "causalBoundary": {
            "availableInformation": [
                "Digest-bound initial parameters and memory, decoder-visible inputs and targets, exact open forward tensors, promoted open output-head backward source, and frozen predicates.",
                "Retained train_h, output-head, ln_g_40, ln_b_40, and ff_bias2_19 gradients only after both corresponding open payloads are complete.",
            ],
            "forbiddenInformation": [
                "Teacher probabilities, teacher activations as calculation inputs, captured gradient values, post-update parameters, future symbols, fitted corrections, or LibNC/NNCP execution.",
                "Claiming a transformer-block backward, recursive training, archive, transfer, package, or objective result.",
            ],
        },
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/open-final-hidden-residual.bf16",
            f"results/{CANDIDATE_ID}/open-final-norm-gain-gradient.bf16",
            f"results/{CANDIDATE_ID}/open-final-norm-bias-gradient.bf16",
            f"results/{CANDIDATE_ID}/open-final-norm-input-residual.bf16",
            f"results/{CANDIDATE_ID}/open-ff-bias2-19-gradient.bf16",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
        ],
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            predicate("k-antecedents", "antecedentsPass", "eq", True),
            predicate("k-final-norm-gain-mismatch", "finalNormGainMismatchCount", "gt", 0),
            predicate("k-top-feedforward-bias-mismatch", "topFeedforwardBiasMismatchCount", "gt", 0),
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
            "interactionRisk": 0.35,
            "uncertaintyRisk": 0.45,
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
