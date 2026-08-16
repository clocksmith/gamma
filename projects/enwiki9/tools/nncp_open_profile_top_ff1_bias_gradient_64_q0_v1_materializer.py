#!/usr/bin/env python3
"""Freeze the open FF2-transpose and GEGLU backward projection gate."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_v1_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_top_ff1_bias_gradient_64_q0_v1"
PARENT_ID = "nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T082216196136Z_fc66142d71c1.json"
)
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T082228Z_f0bff9b6df.json"
)
RUNNER = ROOT / "tools/nncp_open_profile_top_ff1_bias_gradient_64_q0_v1.py"
MATERIALIZER = Path(__file__).resolve()
ACTIVATION_DECISION = ROOT / (
    "results/nncp_v33_libnc_activation_backward_parity_v1/decision.json"
)
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"


def measurement(identifier: str, unit: str, definition: str) -> dict[str, str]:
    return {"id": identifier, "unit": unit, "definition": definition}


def predicate(
    identifier: str, measurement_id: str, operator: str, threshold: int | bool
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
    parent_experiment = ROOT / (
        f"operations/adaptive/experiments/{PARENT_ID}.json"
    )
    experiment = json.loads(parent_experiment.read_text())
    experiment["experimentId"] = CANDIDATE_ID
    experiment["proposalId"] = CANDIDATE_ID
    experiment["parent"] = {
        "candidateId": PARENT_ID,
        "revision": {
            "path": PARENT_REVISION.relative_to(ROOT).as_posix(),
            "sha256": f"sha256:{base.sha256(PARENT_REVISION)}",
        },
    }
    experiment["hypothesis"] = {
        "claim": (
            "The source-attributed streaming BF16 dot for ff2_19 transpose, "
            "followed by the measured unfused tanh-GELU derivative and explicit "
            "BF16 operation boundaries, reconstructs the complete top-layer "
            "FF1-output adjoint whose broadcast projection exactly equals the "
            "retained ff_bias1_19 gradient."
        ),
        "falsification": (
            "Any inherited forward mismatch, nonzero ff_bias1_19 mismatch, "
            "replay drift, dead sign control, dependency violation, source "
            "overflow, strict output failure, or resource failure prevents promotion."
        ),
    }
    experiment["changedMechanism"] = (
        "Add one open FF2-transpose residual and GEGLU backward reducer. Use the "
        "promoted exact final-RMS input residual, initial ff2_19 values, fresh "
        "layer-19 FF1 outputs, the source-attributed streaming dot, and the "
        "previously measured unfused tanh-GELU derivative; compare only after "
        "both complete open payloads exist."
    )
    experiment["controls"] = [
        {
            "id": "promoted-exact-tail",
            "role": "treatment",
            "definition": "The schema-valid exact final-RMS residual is the sole incoming gradient and is digest-bound before execution.",
        },
        {
            "id": "retained-top-ff1-bias",
            "role": "comparator",
            "definition": "The retained ff_bias1_19 gradient is opened only after both complete open projections exist.",
        },
        {
            "id": "independent-open-replay",
            "role": "replay",
            "definition": "Two fresh 32-stream forward populations and complete reducers must reproduce byte-identical residual and gradient artifacts.",
        },
        {
            "id": "negated-incoming-residual",
            "role": "negative",
            "definition": "Sign-negating the promoted incoming residual must change the final ff_bias1_19 projection through the complete transpose and GEGLU path.",
        },
    ]
    experiment["causalBoundary"] = {
        "availableInformation": [
            "Digest-bound initial parameters and state, decoder-visible stream fixtures, fresh exact forward FF1 outputs, the promoted open final-RMS input residual, and frozen arithmetic contracts.",
            "The retained ff_bias1_19 comparator only after both open treatment payloads are complete.",
        ],
        "forbiddenInformation": [
            "Teacher probabilities, teacher activations as calculation inputs, captured intermediate adjoints, retained gradient values during calculation, future symbols, fitted corrections, LibNC execution, or tolerance.",
            "Claiming an ff1_19 matrix gradient, earlier normalization or attention backward, complete transformer backward, recursive update, compression, transfer, package, or Hutter result.",
        ],
    }
    experiment["invariants"] = [
        "Every forward layer-input checkpoint remains exact in both populations.",
        "The incoming residual and initial ff2_19 parameter are digest-bound open inputs; no source intermediate adjoint is used.",
        "Treatment and sign control traverse identical FF2-transpose and GEGLU arithmetic.",
        "All candidate-owned outputs are declared prospectively and validated strictly.",
        "The source package and resource use remain within frozen ceilings.",
    ]
    experiment["budget"] = {
        "expectedGrossSavingsBytes": 0,
        "expectedNetSavingsBytes": -2_000_000,
        "maximumAddedPackageBytes": 2_000_000,
    }
    experiment["evidenceClass"] = "oracle"
    replacements = {
        "runner": base.reference(RUNNER, "runner"),
        "materializer": base.reference(MATERIALIZER, "materializer"),
    }
    inputs = [replacements.get(item["id"], item) for item in experiment["inputs"]]
    additions = [
        base.reference(PARENT_RESULT / "decision.json", "tail-decision"),
        base.reference(PARENT_RESULT / "execution.json", "tail-execution"),
        base.reference(PARENT_RESULT / "guard.json", "tail-guard"),
        base.reference(PARENT_REFLECTION, "tail-reflection"),
        base.reference(
            PARENT_RESULT / "open-final-norm-input-residual.bf16",
            "promoted-final-rms-input-residual",
        ),
        base.reference(ACTIVATION_DECISION, "activation-backward-decision"),
    ]
    existing_ids = {item["id"] for item in inputs}
    inputs.extend(item for item in additions if item["id"] not in existing_ids)
    present_paths = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present_paths:
            inputs.append(base.reference(path, base.source_identifier(path)))
            present_paths.add(relative)
    experiment["inputs"] = inputs
    experiment["measurements"] = [
        measurement("antecedentsPass", "boolean", "All bound parent contracts authorize this gate."),
        measurement("streamCount", "streams", "Fresh streams in each population."),
        measurement("sampleCount", "samples", "Interleaved decoder-visible states."),
        measurement("layerInputCheckpointCount", "tensors", "Exact forward layer-input checkpoints in one population."),
        measurement("layerInputMismatchCount", "F32 elements", "Forward checkpoint mismatches across both populations."),
        measurement("maximumLayerInputAbsoluteError", "float32 value", "Maximum forward checkpoint absolute error."),
        measurement("ff2InputResidualElementCount", "BF16 elements", "Complete open FF2-input residual population."),
        measurement("ff1OutputResidualElementCount", "BF16 elements", "Complete open FF1-output residual population."),
        measurement("topFf1BiasElementCount", "BF16 elements", "Open ff_bias1_19 gradient elements."),
        measurement("topFf1BiasMismatchCount", "BF16 elements", "Open versus retained ff_bias1_19 mismatches."),
        measurement("maximumTopFf1BiasAbsoluteError", "float32 value", "Maximum ff_bias1_19 absolute error."),
        measurement("openBackwardDeterministic", "boolean", "Both complete open populations and reducers are byte-identical."),
        measurement("negatedTopFf1ControlDiffers", "boolean", "Sign control changes the ff_bias1_19 projection."),
        measurement("forbiddenDynamicDependencyCount", "libraries", "Forbidden runtime libraries in open executables."),
        measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed source package size."),
        measurement("guardedWorkRootPass", "boolean", "Candidate work root is removed before finalization."),
    ]
    experiment["promotionPredicates"] = [
        predicate("p-antecedents", "antecedentsPass", "eq", True),
        predicate("p-streams", "streamCount", "eq", 32),
        predicate("p-samples", "sampleCount", "eq", 2048),
        predicate("p-checkpoints", "layerInputCheckpointCount", "eq", 640),
        predicate("p-layer-mismatch", "layerInputMismatchCount", "eq", 0),
        predicate("p-layer-maximum", "maximumLayerInputAbsoluteError", "eq", 0),
        predicate("p-ff2-residual-count", "ff2InputResidualElementCount", "eq", 6_291_456),
        predicate("p-ff1-residual-count", "ff1OutputResidualElementCount", "eq", 12_582_912),
        predicate("p-bias-count", "topFf1BiasElementCount", "eq", 6_144),
        predicate("p-bias-mismatch", "topFf1BiasMismatchCount", "eq", 0),
        predicate("p-bias-maximum", "maximumTopFf1BiasAbsoluteError", "eq", 0),
        predicate("p-replay", "openBackwardDeterministic", "eq", True),
        predicate("p-control", "negatedTopFf1ControlDiffers", "eq", True),
        predicate("p-dependencies", "forbiddenDynamicDependencyCount", "eq", 0),
        predicate("p-source", "incrementalSourceBytes", "lte", 2_000_000),
        predicate("p-work-root", "guardedWorkRootPass", "eq", True),
    ]
    experiment["killPredicates"] = [
        predicate("k-antecedents", "antecedentsPass", "eq", True),
        predicate("k-bias-mismatch", "topFf1BiasMismatchCount", "gt", 0),
    ]
    experiment["outputs"] = [
        f"results/{CANDIDATE_ID}/decision.json",
        f"results/{CANDIDATE_ID}/execution.json",
        f"results/{CANDIDATE_ID}/open-ff2-input-residual.bf16",
        f"results/{CANDIDATE_ID}/open-ff1-output-residual.bf16",
        f"results/{CANDIDATE_ID}/open-ff-bias1-19-gradient.bf16",
        f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
    ]
    experiment["generatedUtc"] = (
        dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    )
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
