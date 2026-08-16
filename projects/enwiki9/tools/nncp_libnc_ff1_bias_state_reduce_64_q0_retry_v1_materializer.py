#!/usr/bin/env python3
"""Freeze the compile-policy-only FF1 bias state-reduction retry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import enwiki9_freeze_implementation_retry as freezer


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_ff1_bias_state_reduce_64_q0_retry_v1"
PARENT_ID = "nncp_libnc_ff1_bias_state_reduce_64_q0_v1"
PARENT_EXPERIMENT = ROOT / f"operations/adaptive/experiments/{PARENT_ID}.json"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T111347680001Z_6388499ba45c.json"
)
RUNNER = ROOT / "tools/nncp_libnc_ff1_bias_state_reduce_64_q0_retry_v1.py"
MATERIALIZER = Path(__file__).resolve()
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
FAILURE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T111413Z_c720568e7a.json"
)
FAILURE_GUARD = ROOT / f"results/{PARENT_ID}/guard.json"


def main() -> int:
    args = argparse.Namespace(
        parent_experiment=PARENT_EXPERIMENT,
        parent_revision=PARENT_REVISION,
        candidate_id=CANDIDATE_ID,
        experiment_id=CANDIDATE_ID,
        runner=RUNNER,
        materializer=MATERIALIZER,
        changed_mechanism=(
            "No arithmetic, population, control, metric, or predicate change. "
            "Add only -Wno-unused-parameter after -Werror so warning-bearing "
            "external LibNC headers compile under the existing strict policy."
        ),
        replace_negative_control_id="reverse-state-order",
        negative_control_id="reverse-state-order",
        negative_control_definition=(
            "The same 32-stream panel reductions are accumulated in reverse "
            "state order and reported without influencing selection."
        ),
        negative_control_measurement_id=None,
        negative_control_measurement_definition=None,
        replace_invariant=[],
        additional_invariant=[
            "The evaluator C arithmetic is byte-identical to the failed parent; only its compiler warning policy changes."
        ],
        evidence=[
            f"compile-failure-reflection={FAILURE_REFLECTION.relative_to(ROOT)}",
            f"compile-failure-guard={FAILURE_GUARD.relative_to(ROOT)}",
        ],
        additional_output=[],
        additional_measurement=[],
        additional_promotion_predicate=[],
        additional_kill_predicate=[],
        strict_output_manifest=True,
        bind_python_source_closure=True,
        output=OUTPUT,
    )
    experiment = freezer.freeze(args)
    print(json.dumps(experiment, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
