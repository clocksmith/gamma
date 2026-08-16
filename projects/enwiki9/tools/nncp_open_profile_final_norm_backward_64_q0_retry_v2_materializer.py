#!/usr/bin/env python3
"""Freeze the BF16 gain-product final RMSNorm backward retry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from enwiki9_freeze_implementation_retry import freeze
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_final_norm_backward_64_q0_retry_v2"
PARENT_ID = "nncp_open_profile_final_norm_backward_64_q0_retry_v1"
PARENT_EXPERIMENT = ROOT / f"operations/adaptive/experiments/{PARENT_ID}.json"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T051403354222Z_5339ca4d5ddf.json"
)
RUNNER = ROOT / "tools/nncp_open_profile_final_norm_backward_64_q0_retry_v2.py"
MATERIALIZER = Path(__file__).resolve()
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T051419Z_4df92ec3b4.json"
)
PARENT_DECISION = ROOT / f"results/{PARENT_ID}/decision.json"
OUTPUT = ROOT / f"operations/adaptive/experiments/{CANDIDATE_ID}.json"
OLD_INVARIANT = (
    "The ln_g_40 broadcast gradient uses 128-sample partial FMA reductions "
    "followed by ordered partial accumulation, matching the promoted "
    "output-head reduction contract."
)
NEW_INVARIANT = (
    "Each per-sample ln_g_40 normalized-state times incoming-gradient product "
    "is rounded to BF16 before 128-sample partial accumulation; reduction "
    "geometry and every other backward operation remain unchanged."
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
            "Preserve the exact centered final RMSNorm input backward and all "
            "upstream work, but round each per-sample normalized-state times "
            "incoming-gradient product to BF16 before the unchanged 128-sample "
            "ln_g_40 reduction."
        ),
        replace_negative_control_id="negated-incoming-residual-retry",
        negative_control_id="negated-incoming-residual-retry-v2",
        negative_control_definition=(
            "A sign-inverted incoming residual traverses the unchanged centered "
            "normalization backward and BF16 gain-product boundary and must change "
            "the top-layer bias projection."
        ),
        negative_control_measurement_id="negatedResidualControlDiffers",
        negative_control_measurement_definition=(
            "Negating the independently generated incoming residual changes the "
            "unchanged exact centered top-layer feedforward-bias projection."
        ),
        replace_invariant=[f"{OLD_INVARIANT}={NEW_INVARIANT}"],
        additional_invariant=[],
        evidence=[
            f"parent-valid-reflection={PARENT_REFLECTION}",
            f"parent-valid-decision={PARENT_DECISION}",
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
            "Rounding each per-sample normalized-state times incoming-gradient "
            "product to BF16 before the frozen reduction reproduces ln_g_40 "
            "exactly while preserving the already exact centered RMSNorm input "
            "residual and every upstream tail."
        ),
        "falsification": (
            "Any inherited antecedent, output-head, promoted-residual, ln_b_40, "
            "centered ff_bias2_19, replay, control, dependency, source, finalization, "
            "or guard failure, or any remaining ln_g_40 mismatch, prevents promotion."
        ),
    }
    OUTPUT.write_text(json.dumps(experiment, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(OUTPUT)
    print(OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
