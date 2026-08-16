#!/usr/bin/env python3
"""Freeze the first production open-backward tail gate."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_output_bias_gradient_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
PARENT_ID = "nncp_ggml_postupdate_forward_parity_64_q1_retry_v2"


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


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    revisions = sorted(
        (ROOT / "operations/adaptive/candidate-revisions" / PARENT_ID).glob("*.json")
    )
    if not revisions:
        raise ValueError("exact-forward parent has no frozen revision")
    parent_revision = revisions[-1]
    inputs = [
        reference(
            ROOT / f"results/{PARENT_ID}/decision.json",
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
        reference(
            ROOT
            / "results/nncp_libnc_profile_update_fixture_64_q3_v1/decision.json",
            "gradient-oracle-decision",
        ),
        reference(
            ROOT
            / "results/nncp_libnc_profile_update_fixture_64_q3_v1/fixture-manifest.json",
            "gradient-oracle-manifest",
        ),
        reference(
            ROOT
            / "results/nncp_libnc_profile_update_fixture_64_q3_v1/guard.json",
            "gradient-oracle-guard",
        ),
        reference(
            ROOT
            / "operations/adaptive/reflections/20260815T235124Z_86c7e4f805.json",
            "gradient-oracle-reflection",
        ),
        reference(
            ROOT
            / "results/nncp_ggml_output_head_update_parity_qm2_v1/decision.json",
            "miniature-output-head-decision",
        ),
        reference(
            ROOT
            / f"results/{PARENT_ID}/ggml_profile_forward_source_closure.tar.xz",
            "exact-forward-source",
        ),
    ]
    measurements = [
        measurement(
            "antecedentsPass",
            "boolean",
            "The exact forward, joint segment transition, gradient oracle, and miniature head-gradient antecedents remain valid and digest-bound.",
        ),
        measurement(
            "streamCount",
            "streams",
            "Complete production streams evaluated from the retained causal input and memory state.",
        ),
        measurement(
            "sampleCount",
            "symbols",
            "Production loss samples evaluated across all streams and states.",
        ),
        measurement(
            "layerInputCheckpointCount",
            "stream-layer tensors",
            "Open attention-input tensors compared against the retained train_h state.",
        ),
        measurement(
            "layerInputMismatchCount",
            "float32 elements",
            "Open layer-input elements that differ from the retained BF16 train_h values.",
        ),
        measurement(
            "maximumLayerInputAbsoluteError",
            "float32 value",
            "Maximum absolute open-versus-retained layer-input difference.",
        ),
        measurement(
            "outputBiasElementCount",
            "gradient elements",
            "Complete production output-bias gradient population.",
        ),
        measurement(
            "outputBiasMismatchCount",
            "gradient elements",
            "Open BF16 output-bias gradient words that differ from the retained comparator.",
        ),
        measurement(
            "maximumOutputBiasAbsoluteError",
            "float32 value",
            "Maximum absolute open-versus-retained output-bias gradient difference.",
        ),
        measurement(
            "openGradientDeterministic",
            "boolean",
            "Two complete open all-stream executions emit byte-identical gradient and checkpoint summaries.",
        ),
        measurement(
            "shiftedTargetControlDiffers",
            "boolean",
            "A cyclic within-stream target shift changes the open gradient payload.",
        ),
        measurement(
            "forbiddenDynamicDependencyCount",
            "dependencies",
            "Dynamic LibNC, NNCP, GGML, CUDA, OpenMP, or BLAS dependencies in the built open executable.",
        ),
        measurement(
            "incrementalSourceBytes",
            "bytes",
            "Compressed dependency-closed orchestration and open-gradient source package.",
        ),
        measurement(
            "guardedWorkRootPass",
            "boolean",
            "All generated builds and forward outputs remained under and were removed with the guarded work root.",
        ),
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
    kill = [
        predicate("k-antecedents", "antecedentsPass", "eq", True),
        predicate("k-layer-input-mismatch", "layerInputMismatchCount", "gt", 0),
        predicate("k-output-bias-mismatch", "outputBiasMismatchCount", "gt", 0),
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
                "path": parent_revision.relative_to(ROOT).as_posix(),
                "sha256": f"sha256:{sha256(parent_revision)}",
            },
        },
        "hypothesis": {
            "claim": "The exact Gamma open forward, evaluated over all 32 production streams, and the explicit decoder-causal negative-log-likelihood residual reproduce every BF16 word of the retained production out_bias gradient without consuming teacher probabilities or gradients as inputs.",
            "falsification": "Any antecedent drift, all-stream layer-input mismatch, output-bias gradient mismatch, replay difference, dead target control, dependency violation, source overflow, or guard failure prevents promotion and forbids an open-backward-tail claim.",
        },
        "changedMechanism": "Replace the captured production out_bias gradient with a fresh open computation from initial parameters, decoder-visible state, input symbols, target symbols, exact forward probabilities, and the frozen 1/(32*64) loss scale.",
        "invariants": [
            "The production geometry, parameters, initial memory, inputs, targets, BF16 boundaries, and exact forward arithmetic remain unchanged.",
            "All 20 attention-input checkpoints for every stream are generated before their retained train_h comparator values are read.",
            "The retained out_bias gradient is opened only after the complete open gradient payload is written.",
            "No teacher probability, internal activation, or gradient payload is used to calculate the open gradient.",
            "A cyclic within-stream target shift is a liveness control only and receives no score or promotion credit.",
            "The closed teacher, LibNC, and NNCP are not executed during retained replay.",
            "This experiment proves at most the production loss-to-output-bias tail; it proves no output-matrix, final-normalization, transformer-layer, embedding, recursive-training, compression, transfer, package, or Hutter claim.",
        ],
        "controls": [
            {
                "id": "exact-open-all-stream-forward",
                "role": "treatment",
                "definition": "The unchanged exact forward is driven independently for every retained production stream and feeds the open loss-tail reduction.",
            },
            {
                "id": "retained-gradient-oracle",
                "role": "comparator",
                "definition": "The captured BF16 out_bias gradient is read only after the fresh open payload is complete.",
            },
            {
                "id": "independent-open-replay",
                "role": "replay",
                "definition": "The complete 32-stream forward and gradient reduction execute twice and must reproduce identical bytes.",
            },
            {
                "id": "cyclic-target-shift",
                "role": "negative",
                "definition": "Targets are shifted by one state within each stream while probabilities remain fixed; the resulting gradient must differ.",
            },
        ],
        "population": {
            "unit": "one production stream-layer checkpoint or output-bias gradient word",
            "scopeBytes": None,
            "scopeSymbols": 2048,
            "selection": "All 32 streams, all 64 states, all 20 layer attention inputs, and all 16,392 output-bias gradient words at the first retained production update boundary.",
            "coordinate": "Production update over original transformed-symbol coordinates [256,320) independently within each of 32 contiguous streams.",
        },
        "causalBoundary": {
            "availableInformation": [
                "Digest-bound initial parameters and recurrent memory, decoder-visible inputs, decoded targets, fixed source, and frozen predicates.",
                "Retained train_h checkpoints and out_bias gradient only after each corresponding open output is complete.",
            ],
            "forbiddenInformation": [
                "Teacher probabilities, teacher internal activations as calculation inputs, captured gradient values, post-update parameters, future symbols, fitted corrections, or LibNC/NNCP execution.",
                "Claiming any broader backward, recursive-training, archive, transfer, package, or objective result.",
            ],
        },
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/open-out-bias-gradient.bf16",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
        ],
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": kill,
        "budget": {
            "expectedGrossSavingsBytes": 0,
            "maximumAddedPackageBytes": 2_000_000,
            "expectedNetSavingsBytes": -2_000_000,
        },
        "search": {
            "expectedTransferRetention": 1.0,
            "expectedRuntimeRatio": 1.0,
            "expectedMemoryRatio": 1.0,
            "uncertaintyRisk": 0.3,
            "interactionRisk": 0.2,
        },
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "outputManifestPolicy": "complete-result-artifacts-v1",
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
