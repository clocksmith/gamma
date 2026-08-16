#!/usr/bin/env python3
"""Freeze the exact-FF2 open top-FF1 bias projection retry."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_open_profile_top_ff1_bias_gradient_64_q0_v1_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v1"
PARENT_ID = "nncp_open_profile_top_ff1_bias_gradient_64_q0_v1"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T084738538470Z_6b8e56c63be9.json"
)
PARENT_EXPERIMENT = ROOT / f"operations/adaptive/experiments/{PARENT_ID}.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T084751Z_2949ede196.json"
)
RUNNER = ROOT / "tools/nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v1.py"
MATERIALIZER = Path(__file__).resolve()
BLOCK_RESULT = ROOT / "results/nncp_libnc_ff2_transpose_block128_64_q0_v1"
BLOCK_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T093907Z_7f51e2d346.json"
)
SOURCE_RESULT = ROOT / "results/nncp_libnc_top_ff2_input_adjoint_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
contracts = base.base


def measurement(identifier: str, unit: str, definition: str) -> dict[str, str]:
    return {"id": identifier, "unit": unit, "definition": definition}


def predicate(
    identifier: str,
    measurement_id: str,
    operator: str,
    threshold: int | bool,
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
    experiment = json.loads(PARENT_EXPERIMENT.read_text())
    experiment["experimentId"] = CANDIDATE_ID
    experiment["proposalId"] = CANDIDATE_ID
    experiment["parent"] = {
        "candidateId": PARENT_ID,
        "revision": {
            "path": PARENT_REVISION.relative_to(ROOT).as_posix(),
            "sha256": f"sha256:{contracts.sha256(PARENT_REVISION)}",
        },
    }
    experiment["hypothesis"] = {
        "claim": (
            "Replacing only the FF2 transpose with the source-exact ordered "
            "128-feature panel schedule preserves the exact upstream residual "
            "and reconstructs the retained ff_bias1_19 gradient through the "
            "frozen GEGLU backward contract."
        ),
        "falsification": (
            "Any antecedent, forward, source-adjoint, retained-gradient, replay, "
            "control, dependency, source-size, strict-output, or resource failure "
            "prevents promotion."
        ),
    }
    experiment["changedMechanism"] = (
        "Replace only the horizontal FF2 transpose dot with adjacent output-feature "
        "SIMD lanes whose accumulators reset for each ordered 128-feature reduction "
        "panel and whose completed panels are added in order. Preserve every forward, "
        "GEGLU, BF16, projection, control, and comparison boundary."
    )
    experiment["controls"] = [
        {
            "id": "source-exact-ff2-transpose",
            "role": "treatment",
            "definition": (
                "The promoted 128-panel mechanism must independently reproduce the "
                "complete captured FF2-input adjoint before the retained bias can pass."
            ),
        },
        {
            "id": "retained-top-ff1-bias",
            "role": "comparator",
            "definition": (
                "The retained ff_bias1_19 gradient is opened only after each complete "
                "open projection exists."
            ),
        },
        {
            "id": "independent-open-replay",
            "role": "replay",
            "definition": (
                "Two fresh 32-stream forward populations and complete reducers must "
                "produce byte-identical artifacts."
            ),
        },
        {
            "id": "negated-incoming-residual",
            "role": "negative",
            "definition": (
                "Sign-negating the same incoming residual must change the projected "
                "ff_bias1_19 gradient."
            ),
        },
    ]
    experiment["causalBoundary"] = {
        "availableInformation": [
            "Digest-bound initial parameters and state, fresh exact forward FF1 outputs, the promoted open final-RMS input residual, and the prospectively frozen 128-panel transpose arithmetic.",
            "The captured FF2-input adjoint and retained ff_bias1_19 gradient only as comparators after each complete open payload exists.",
        ],
        "forbiddenInformation": [
            "Teacher probabilities or activations as calculation inputs, captured adjoints or retained gradients during calculation, future symbols, fitted corrections, LibNC execution, coordinate repair, or tolerance.",
            "Claiming complete transformer backward, a recursive update, compression, transfer, package, or Hutter credit from this oracle gate.",
        ],
    }
    experiment["invariants"] = [
        "Every forward layer-input checkpoint remains exact in both populations.",
        "Only the FF2 transpose arithmetic differs from the immutable parent candidate.",
        "The source FF2 adjoint and retained FF1 bias are independent comparators, never calculation inputs.",
        "Treatment and sign control traverse identical transpose and GEGLU arithmetic.",
        "All candidate outputs, source closure, and resource ceilings remain prospectively frozen.",
    ]
    experiment["budget"] = {
        "expectedGrossSavingsBytes": 0,
        "expectedNetSavingsBytes": -2_000_000,
        "maximumAddedPackageBytes": 2_000_000,
    }
    experiment["evidenceClass"] = "oracle"
    replacements = {
        "runner": contracts.reference(RUNNER, "runner"),
        "materializer": contracts.reference(MATERIALIZER, "materializer"),
    }
    inputs = [replacements.get(item["id"], item) for item in experiment["inputs"]]
    additions = [
        contracts.reference(PARENT_REFLECTION, "parent-reflection"),
        contracts.reference(BLOCK_RESULT / "decision.json", "block128-decision"),
        contracts.reference(BLOCK_RESULT / "execution.json", "block128-execution"),
        contracts.reference(BLOCK_RESULT / "guard.json", "block128-guard"),
        contracts.reference(BLOCK_REFLECTION, "block128-reflection"),
        contracts.reference(
            BLOCK_RESULT / "block128-ff2-input-adjoint.bf16",
            "block128-ff2-input-adjoint",
        ),
        contracts.reference(
            SOURCE_RESULT / "decision.json", "source-ff2-input-adjoint-decision"
        ),
        contracts.reference(
            SOURCE_RESULT / "source-ff2-input-adjoint.bf16",
            "source-ff2-input-adjoint",
        ),
    ]
    existing_ids = {item["id"] for item in inputs}
    inputs.extend(item for item in additions if item["id"] not in existing_ids)
    present_paths = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present_paths:
            inputs.append(
                contracts.reference(path, contracts.source_identifier(path))
            )
            present_paths.add(relative)
    experiment["inputs"] = inputs
    experiment["measurements"].extend(
        [
            measurement(
                "sourceFf2InputResidualMismatchCount",
                "BF16 elements",
                "Open 128-panel FF2 residual mismatches against the captured source adjoint.",
            ),
            measurement(
                "maximumSourceFf2InputResidualAbsoluteError",
                "float32 value",
                "Maximum open versus captured FF2-input residual absolute error.",
            ),
        ]
    )
    experiment["promotionPredicates"].extend(
        [
            predicate(
                "p-source-ff2-mismatch",
                "sourceFf2InputResidualMismatchCount",
                "eq",
                0,
            ),
            predicate(
                "p-source-ff2-maximum",
                "maximumSourceFf2InputResidualAbsoluteError",
                "eq",
                0,
            ),
        ]
    )
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
