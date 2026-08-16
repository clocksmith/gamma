#!/usr/bin/env python3
"""Freeze the centered final RMSNorm backward implementation retry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from enwiki9_freeze_implementation_retry import freeze
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_final_norm_backward_64_q0_retry_v1"
PARENT_ID = "nncp_open_profile_final_norm_backward_64_q0_v1"
PARENT_EXPERIMENT = ROOT / f"operations/adaptive/experiments/{PARENT_ID}.json"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T045642195441Z_9fbf51f9725b.json"
)
RUNNER = ROOT / "tools/nncp_open_profile_final_norm_backward_64_q0_retry.py"
MATERIALIZER = Path(__file__).resolve()
FAILED_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T045714Z_6eb299ed8d.json"
)
FAILED_GUARD = ROOT / f"results/{PARENT_ID}/guard.json"
FAILED_GAIN = ROOT / f"results/{PARENT_ID}/open-final-norm-gain-gradient.bf16"
FAILED_PROJECTION = ROOT / f"results/{PARENT_ID}/open-ff-bias2-19-gradient.bf16"
CONCAT_DECISION = ROOT / (
    "results/nncp_v33_libnc_concat_rmsnorm_backward_contract_v1/decision.json"
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
            "Preserve the complete open forward and output-head backward, but reduce "
            "ln_g_40 in the already proved 128-sample chunked FMA order, apply the "
            "measured concat-root RMSNorm input backward with both mean-gradient and "
            "output-weighted centering terms, and cache output counts before cleanup."
        ),
        replace_negative_control_id="negated-incoming-residual",
        negative_control_id="negated-incoming-residual-retry",
        negative_control_definition=(
            "A sign-inverted incoming residual traverses the corrected centered "
            "normalization backward and must change the top-layer bias projection."
        ),
        negative_control_measurement_id="negatedResidualControlDiffers",
        negative_control_measurement_definition=(
            "Negating the independently generated incoming residual changes the "
            "corrected centered top-layer feedforward-bias projection."
        ),
        replace_invariant=[],
        additional_invariant=[
            "The ln_g_40 broadcast gradient uses 128-sample partial FMA reductions "
            "followed by ordered partial accumulation, matching the promoted "
            "output-head reduction contract.",
            "The concat-root final RMSNorm input residual is inverse times gradient "
            "minus mean-gradient minus normalized-output times mean of gradient "
            "times normalized-output.",
            "All output element counts are cached from persisted result artifacts "
            "before the guarded work root is removed.",
        ],
        evidence=[
            f"failed-attempt-reflection={FAILED_REFLECTION}",
            f"failed-attempt-guard={FAILED_GUARD}",
            f"failed-ln-g-diagnostic={FAILED_GAIN}",
            f"failed-ff-bias-projection={FAILED_PROJECTION}",
            f"concat-rmsnorm-contract={CONCAT_DECISION}",
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
            "The frozen 128-sample gain-gradient reduction and measured concat-root "
            "centered RMSNorm input backward reproduce ln_g_40, ln_b_40, and the "
            "ff_bias2_19 projection exactly while preserving the complete open "
            "output-head tail."
        ),
        "falsification": (
            "Any inherited antecedent or tail mismatch, promoted-residual mismatch, "
            "ln_g_40 or ln_b_40 mismatch, centered ff_bias2_19 projection mismatch, "
            "replay difference, dead control, dependency violation, source overflow, "
            "finalization error, or guard failure prevents promotion."
        ),
    }
    OUTPUT.write_text(json.dumps(experiment, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(OUTPUT)
    print(OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
