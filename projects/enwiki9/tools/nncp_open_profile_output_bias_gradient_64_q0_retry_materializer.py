#!/usr/bin/env python3
"""Freeze the BF16-boundary output-bias gradient retry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from enwiki9_freeze_implementation_retry import freeze


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_output_bias_gradient_64_q0_retry_v1"
PARENT_ID = "nncp_open_profile_output_bias_gradient_64_q0_v1"
PARENT_EXPERIMENT = ROOT / f"operations/adaptive/experiments/{PARENT_ID}.json"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T031146382932Z_4067f537ac3a.json"
)
RUNNER = ROOT / "tools/nncp_open_profile_output_bias_gradient_64_q0_retry.py"
MATERIALIZER = Path(__file__).resolve()
FAILED_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T031213Z_57a9477621.json"
)
FAILED_GUARD = ROOT / f"results/{PARENT_ID}/guard.json"
OUTPUT = ROOT / f"operations/adaptive/experiments/{CANDIDATE_ID}.json"
OLD_INVARIANT = (
    "A cyclic within-stream target shift is a liveness control only and receives "
    "no score or promotion credit."
)
NEW_INVARIANT = (
    "A cyclic vocabulary-successor target remap is a liveness control only and "
    "receives no score or promotion credit."
)


def main() -> int:
    args = argparse.Namespace(
        parent_experiment=PARENT_EXPERIMENT,
        parent_revision=PARENT_REVISION,
        candidate_id=CANDIDATE_ID,
        experiment_id=CANDIDATE_ID,
        runner=RUNNER,
        materializer=MATERIALIZER,
        changed_mechanism=(
            "Preserve the exact all-stream forward and loss residual, but round each "
            "per-sample F32 logit residual to BF16 before the broadcast-bias reduction; "
            "package the candidate-owned forward materializer explicitly and replace the "
            "histogram-invariant state permutation with a vocabulary-successor target remap."
        ),
        replace_negative_control_id="cyclic-target-shift",
        negative_control_id="cyclic-vocabulary-target-shift",
        negative_control_definition=(
            "Each target is replaced by its cyclic successor in the production vocabulary "
            "while probabilities remain fixed; the resulting gradient must differ."
        ),
        negative_control_measurement_id="shiftedTargetControlDiffers",
        negative_control_measurement_definition=(
            "A cyclic vocabulary-successor target remap changes the open gradient payload."
        ),
        replace_invariant=[f"{OLD_INVARIANT}={NEW_INVARIANT}"],
        additional_invariant=[
            "Every per-sample output residual crosses the production F32-to-BF16 logit "
            "boundary before the bias-broadcast reduction."
        ],
        evidence=[
            f"failed-attempt-reflection={FAILED_REFLECTION}",
            f"failed-attempt-guard={FAILED_GUARD}",
        ],
        additional_output=[],
        additional_measurement=[],
        additional_promotion_predicate=[],
        additional_kill_predicate=[],
        strict_output_manifest=True,
        bind_python_source_closure=True,
        output=OUTPUT,
    )
    print(json.dumps(freeze(args), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
