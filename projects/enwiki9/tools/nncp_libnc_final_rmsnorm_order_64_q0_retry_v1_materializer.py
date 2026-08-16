#!/usr/bin/env python3
"""Freeze the declared-probe retry for final-RMSNorm order attribution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from enwiki9_freeze_implementation_retry import freeze, reference
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_final_rmsnorm_order_64_q0_retry_v1"
PARENT_ID = "nncp_libnc_final_rmsnorm_order_64_q0_v1"
PARENT_EXPERIMENT = ROOT / f"operations/adaptive/experiments/{PARENT_ID}.json"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T071949631003Z_f4d935c9e722.json"
)
RUNNER = ROOT / "tools/nncp_libnc_final_rmsnorm_order_64_q0_retry_v1.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
FAILED_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T072040Z_e4976727fd.json"
)
FAILED_GUARD = ROOT / f"results/{PARENT_ID}/guard.json"
OUTPUT = ROOT / f"operations/adaptive/experiments/{CANDIDATE_ID}.json"


def replace_input(
    experiment: dict[str, object], identifier: str, path: Path
) -> None:
    inputs = experiment["inputs"]
    if not isinstance(inputs, list):
        raise ValueError("retry experiment inputs are not a list")
    matches = [
        index for index, item in enumerate(inputs) if item.get("id") == identifier
    ]
    if len(matches) != 1:
        raise ValueError(f"retry input replacement is not unique: {identifier}")
    inputs[matches[0]] = reference(path, identifier)


def main() -> int:
    args = argparse.Namespace(
        parent_experiment=PARENT_EXPERIMENT,
        parent_revision=PARENT_REVISION,
        candidate_id=CANDIDATE_ID,
        experiment_id=CANDIDATE_ID,
        runner=RUNNER,
        materializer=MATERIALIZER,
        changed_mechanism=(
            "Preserve the read-only production capture, exact forward replay, "
            "six arithmetic orders, comparators, controls, and prospective "
            "predicates, but declare the two probe functions at the unique "
            "pre-trf_eval boundary before their first use."
        ),
        replace_negative_control_id="negated-incoming-residual",
        negative_control_id="negated-incoming-residual-retry-v1",
        negative_control_definition=(
            "Sign-negating the complete incoming residual must still change the "
            "reconstructed input adjoint after the declaration-only fix."
        ),
        negative_control_measurement_id="negatedControlDiffers",
        negative_control_measurement_definition=(
            "Sign-negating the complete incoming residual changes the "
            "reconstructed input adjoint in the declaration-only retry."
        ),
        replace_invariant=[],
        additional_invariant=[
            (
                "Forward declarations change only C translation-unit validity; "
                "they introduce no runtime state, tensor, operation, value, or branch."
            )
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
    experiment = freeze(args)
    replace_input(
        experiment,
        "probe-source",
        PROGRAM / "final_rmsnorm_probe.inc.c",
    )
    replace_input(
        experiment,
        "evaluator-source",
        PROGRAM / "final_rmsnorm_order.cpp",
    )
    replace_input(experiment, "program-descriptor", PROGRAM / "program.py")
    experiment["causalBoundary"]["availableInformation"].append(
        "The failed attempt exposed only a compiler declaration-order error and "
        "no source tensor, arithmetic-order comparison, or scientific measurement."
    )
    experiment["causalBoundary"]["forbiddenInformation"].append(
        "Any scientific-predicate, capture, evaluator, order-family, coordinate, "
        "comparator, or teacher-operation change in this implementation retry."
    )
    OUTPUT.write_text(json.dumps(experiment, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(OUTPUT)
    print(OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
