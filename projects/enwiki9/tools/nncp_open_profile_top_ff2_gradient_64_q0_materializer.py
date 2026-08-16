#!/usr/bin/env python3
"""Freeze the production open top-layer FF2 parameter-gradient gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from enwiki9_freeze_implementation_retry import freeze
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_top_ff2_gradient_64_q0_v1"
PARENT_ID = "nncp_open_profile_final_norm_backward_64_q0_retry_v2"
PARENT_EXPERIMENT = ROOT / f"operations/adaptive/experiments/{PARENT_ID}.json"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T053148075770Z_2aa6a39d41e4.json"
)
RUNNER = ROOT / "tools/nncp_open_profile_top_ff2_gradient_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T053159Z_b79233ecb1.json"
)
PARENT_DECISION = ROOT / f"results/{PARENT_ID}/decision.json"
PARENT_HIDDEN_RESIDUAL = ROOT / (
    f"results/{PARENT_ID}/open-final-hidden-residual.bf16"
)
OUTPUT = ROOT / f"operations/adaptive/experiments/{CANDIDATE_ID}.json"


def main() -> int:
    args = argparse.Namespace(
        parent_experiment=PARENT_EXPERIMENT,
        parent_revision=PARENT_REVISION,
        candidate_id=CANDIDATE_ID,
        experiment_id=CANDIDATE_ID,
        runner=RUNNER,
        materializer=MATERIALIZER,
        changed_mechanism=(
            "Retain the exact output-head and centered final-normalization "
            "backward, expose each freshly generated BF16 layer-19 GEGLU "
            "output, and reduce its outer product with the centered residual "
            "into the complete ff2_19 parameter gradient using the already "
            "proved 128-sample matmul reduction."
        ),
        replace_negative_control_id=None,
        negative_control_id="negated-top-ff2-upstream",
        negative_control_definition=(
            "Sign-negating the complete centered top-layer residual while "
            "holding every fresh GEGLU activation fixed must change the "
            "complete ff2_19 parameter gradient."
        ),
        negative_control_measurement_id=None,
        negative_control_measurement_definition=None,
        replace_invariant=[],
        additional_invariant=[
            (
                "Every ff2_19 word is generated from fresh open GEGLU "
                "activations and the exact centered residual before the "
                "retained ff2_19 comparator is read."
            ),
            (
                "The ff2_19 outer-product reduction uses 128-sample partial "
                "FMA accumulation and ordered partial addition without a "
                "teacher activation or captured gradient as input."
            ),
            (
                "This experiment proves only the top-layer FF2 parameter "
                "gradient; it proves no FF2 activation residual, GEGLU "
                "backward, recursive update, compression, or Hutter result."
            ),
        ],
        evidence=[
            f"final-norm-backward-reflection={PARENT_REFLECTION}",
            f"final-norm-backward-decision={PARENT_DECISION}",
            f"promoted-final-norm-hidden-residual={PARENT_HIDDEN_RESIDUAL}",
        ],
        additional_output=[
            f"results/{CANDIDATE_ID}/open-ff2-19-gradient.bf16"
        ],
        additional_measurement=[
            (
                "topFf2ElementCount=gradient elements="
                "Complete production ff2_19 parameter-gradient population."
            ),
            (
                "topFf2MismatchCount=gradient elements="
                "Open BF16 ff2_19 words that differ from the delayed retained "
                "comparator."
            ),
            (
                "maximumTopFf2AbsoluteError=float32 value="
                "Maximum absolute open-versus-retained ff2_19 difference."
            ),
            (
                "negatedTopFf2ControlDiffers=boolean="
                "Negating the centered top-layer residual changes the complete "
                "ff2_19 gradient."
            ),
        ],
        additional_promotion_predicate=[
            "p-topff2elementcount=topFf2ElementCount=eq=3145728",
            "p-topff2mismatchcount=topFf2MismatchCount=eq=0",
            "p-maximumtopff2absoluteerror=maximumTopFf2AbsoluteError=eq=0",
            (
                "p-negatedtopff2controldiffers="
                "negatedTopFf2ControlDiffers=eq=true"
            ),
        ],
        additional_kill_predicate=[
            "k-topff2mismatch=topFf2MismatchCount=gt=0"
        ],
        strict_output_manifest=True,
        bind_python_source_closure=True,
        output=OUTPUT,
    )
    experiment = freeze(args)
    experiment["hypothesis"] = {
        "claim": (
            "The promoted centered final-normalization input residual and "
            "freshly generated BF16 layer-19 GEGLU output reproduce every "
            "retained ff2_19 parameter-gradient word under the already proved "
            "128-sample matmul reduction."
        ),
        "falsification": (
            "Any inherited tail failure, replay mismatch, dead control, "
            "dependency or guard violation, source overflow, population drift, "
            "or one differing ff2_19 word prevents promotion and forbids a "
            "top-layer FF2 parameter-gradient claim."
        ),
    }
    experiment["population"]["selection"] = (
        "All inherited exact forward, output-head, final RMSNorm, and "
        "ff_bias2_19 populations plus all 3,145,728 BF16 ff2_19 gradient words "
        "at the first retained production update."
    )
    experiment["causalBoundary"]["availableInformation"].append(
        "Fresh open layer-19 GEGLU activations and the freshly reconstructed "
        "centered final-normalization residual; retained ff2_19 values only "
        "after both treatment and replay payloads are complete."
    )
    experiment["causalBoundary"]["forbiddenInformation"].append(
        "Captured ff2_19 values as calculation inputs, teacher activations, "
        "an unmeasured reduction order, or any FF2 activation-residual claim."
    )
    OUTPUT.write_text(json.dumps(experiment, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(OUTPUT)
    print(OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
