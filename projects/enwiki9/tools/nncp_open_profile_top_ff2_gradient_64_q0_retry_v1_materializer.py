#!/usr/bin/env python3
"""Freeze the BF16 affine-upstream top-layer FF2 gradient retry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from enwiki9_freeze_implementation_retry import freeze
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_top_ff2_gradient_64_q0_retry_v1"
PARENT_ID = "nncp_open_profile_top_ff2_gradient_64_q0_v1"
PARENT_EXPERIMENT = ROOT / f"operations/adaptive/experiments/{PARENT_ID}.json"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T055538160747Z_2328e90b16fc.json"
)
RUNNER = ROOT / "tools/nncp_open_profile_top_ff2_gradient_64_q0_retry_v1.py"
MATERIALIZER = Path(__file__).resolve()
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T055603Z_52a69ff065.json"
)
PARENT_DECISION = ROOT / f"results/{PARENT_ID}/decision.json"
PARENT_HIDDEN_RESIDUAL = ROOT / (
    f"results/{PARENT_ID}/open-final-hidden-residual.bf16"
)
OUTPUT = ROOT / f"operations/adaptive/experiments/{CANDIDATE_ID}.json"
OLD_INVARIANT = (
    "Each per-sample ln_g_40 normalized-state times incoming-gradient product "
    "is rounded to BF16 before 128-sample partial accumulation; reduction "
    "geometry and every other backward operation remain unchanged."
)
NEW_INVARIANT = (
    "Each per-sample ln_g_40 normalized-state times incoming-gradient product "
    "and each final RMSNorm incoming-gradient times gain product is rounded "
    "to BF16 at its tensor boundary; the centered formula, reductions, and "
    "every other backward operation remain unchanged."
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
            "Preserve every forward, output-head, gain-gradient, centered "
            "normalization, and FF2 reduction operation, but round the "
            "per-element final RMSNorm incoming-gradient times gain product "
            "to BF16 before calculating the centered input residual."
        ),
        replace_negative_control_id="negated-top-ff2-upstream",
        negative_control_id="negated-top-ff2-upstream-retry-v1",
        negative_control_definition=(
            "Sign-negating the incoming residual must remain live through the "
            "new BF16 affine-product boundary, centered normalization backward, "
            "and complete ff2_19 reduction."
        ),
        negative_control_measurement_id="negatedTopFf2ControlDiffers",
        negative_control_measurement_definition=(
            "Negating the incoming residual before the BF16 affine-product "
            "boundary changes the complete ff2_19 gradient."
        ),
        replace_invariant=[f"{OLD_INVARIANT}={NEW_INVARIANT}"],
        additional_invariant=[
            (
                "The retained ff2_19 comparator is not used to select or "
                "correct coordinates; the single BF16 affine boundary applies "
                "uniformly to the complete population."
            )
        ],
        evidence=[
            f"parent-ff2-reflection={PARENT_REFLECTION}",
            f"parent-ff2-decision={PARENT_DECISION}",
            f"promoted-parent-ff2-hidden-residual={PARENT_HIDDEN_RESIDUAL}",
        ],
        additional_output=[],
        additional_measurement=[],
        additional_promotion_predicate=[],
        additional_kill_predicate=[],
        strict_output_manifest=True,
        bind_python_source_closure=True,
        output=OUTPUT,
    )
    experiment = freeze(args)
    experiment["hypothesis"] = {
        "claim": (
            "Rounding the final RMSNorm incoming-gradient times gain product "
            "to BF16 before the frozen centered backward eliminates the sparse "
            "coordinate-localized ff2_19 mismatches while preserving every "
            "inherited exact tail."
        ),
        "falsification": (
            "Any inherited predicate failure, dead control, replay difference, "
            "dependency or guard violation, source overflow, ff_bias2_19 "
            "regression, or one remaining ff2_19 mismatch refutes the BF16 "
            "affine-upstream hypothesis and prevents promotion."
        ),
    }
    experiment["causalBoundary"]["availableInformation"].append(
        "The parent mismatch count and its coordinate concentration justify "
        "one uniform BF16 affine-product boundary; no retained gradient value "
        "is available during calculation."
    )
    experiment["causalBoundary"]["forbiddenInformation"].append(
        "Coordinate-specific patches, comparator-derived residuals, tolerance, "
        "or any change to the frozen FF2 reduction order."
    )
    OUTPUT.write_text(json.dumps(experiment, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(OUTPUT)
    print(OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
