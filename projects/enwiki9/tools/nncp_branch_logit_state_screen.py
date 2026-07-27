#!/usr/bin/env python3
"""Screen a rational-odds recurrent logit student on an NNCP branch trace."""

from __future__ import annotations

import argparse
from collections import defaultdict
from fractions import Fraction
import hashlib
import json
import lzma
import math
from pathlib import Path
import struct

from nncp_branch_affine_state_screen import (
    HALF,
    SHIFTS,
    materialize_samples,
    round_div,
    round_fraction,
)
from nncp_branch_centroid_screen import TOTAL, load, loss


ODDS_NUMERATOR = 257
ODDS_DENOMINATOR = 256
MAX_SCORE = 2048
LOG_BASE = math.log(ODDS_NUMERATOR / ODDS_DENOMINATOR)
WEIGHT_RIDGE = 1.0
INTERCEPT_RIDGE = 1.0
NEWTON_STEPS = 12
MODEL_MAGIC = b"NNLGS1\0\0"
DIMENSION = 2 * len(SHIFTS)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def logistic(value: float) -> float:
    if value >= 0:
        inverse = math.exp(-min(value, 60.0))
        return 1.0 / (1.0 + inverse)
    direct = math.exp(max(value, -60.0))
    return direct / (1.0 + direct)


def solve_float(matrix: list[list[float]], vector: list[float]) -> list[float]:
    size = len(vector)
    augmented = [row[:] + [vector[index]] for index, row in enumerate(matrix)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-15:
            raise ValueError("singular Newton system")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        scale = augmented[column][column]
        augmented[column] = [value / scale for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            if factor:
                augmented[row] = [
                    left - factor * right
                    for left, right in zip(augmented[row], augmented[column])
                ]
    return [augmented[index][-1] for index in range(size)]


def target(sample: dict[str, object], target_name: str) -> float:
    if target_name == "teacher":
        return int(sample["teacher"]) / TOTAL
    return 1.0 if int(sample["bit"]) == 0 else 0.0


def objective(
    samples: list[dict[str, object]],
    target_name: str,
    intercepts: dict[tuple[int, int], float],
    weights: list[float],
) -> float:
    value = 0.5 * WEIGHT_RIDGE * sum(weight * weight for weight in weights)
    value += 0.5 * INTERCEPT_RIDGE * sum(
        intercept * intercept for intercept in intercepts.values()
    )
    for sample in samples:
        node = sample["node"]
        features = sample["features"]
        assert isinstance(node, tuple)
        assert isinstance(features, tuple)
        score = intercepts[node] + sum(
            weight * feature / HALF
            for weight, feature in zip(weights, features)
        )
        probability = min(1.0 - 1e-15, max(1e-15, logistic(score)))
        wanted = target(sample, target_name)
        value -= wanted * math.log(probability)
        value -= (1.0 - wanted) * math.log(1.0 - probability)
    return value


def fit(
    samples: list[dict[str, object]], target_name: str, stateful: bool
) -> dict[str, object]:
    sums: dict[tuple[int, int], float] = defaultdict(float)
    counts: dict[tuple[int, int], int] = defaultdict(int)
    for sample in samples:
        node = sample["node"]
        assert isinstance(node, tuple)
        sums[node] += target(sample, target_name)
        counts[node] += 1
    intercepts = {}
    for node in sorted(counts):
        probability = (sums[node] + 0.5 * INTERCEPT_RIDGE) / (
            counts[node] + INTERCEPT_RIDGE
        )
        intercepts[node] = math.log(probability / (1.0 - probability))
    weights = [0.0] * DIMENSION

    for _ in range(NEWTON_STEPS):
        gradient_node = {
            node: INTERCEPT_RIDGE * value for node, value in intercepts.items()
        }
        diagonal_node = {node: INTERCEPT_RIDGE for node in intercepts}
        cross_node = {
            node: [0.0] * DIMENSION for node in intercepts
        }
        gradient_weight = [WEIGHT_RIDGE * value for value in weights]
        hessian = [
            [
                WEIGHT_RIDGE if left == right else 0.0
                for right in range(DIMENSION)
            ]
            for left in range(DIMENSION)
        ]
        for sample in samples:
            node = sample["node"]
            raw_features = sample["features"]
            assert isinstance(node, tuple)
            assert isinstance(raw_features, tuple)
            features = [value / HALF for value in raw_features]
            score = intercepts[node] + sum(
                weight * feature for weight, feature in zip(weights, features)
            )
            probability = logistic(score)
            variance = max(1e-9, probability * (1.0 - probability))
            residual = probability - target(sample, target_name)
            gradient_node[node] += residual
            diagonal_node[node] += variance
            for left in range(DIMENSION):
                gradient_weight[left] += residual * features[left]
                cross_node[node][left] += variance * features[left]
                for right in range(DIMENSION):
                    hessian[left][right] += (
                        variance * features[left] * features[right]
                    )

        if stateful:
            schur = [row[:] for row in hessian]
            right = [-value for value in gradient_weight]
            for node in intercepts:
                denominator = diagonal_node[node]
                cross = cross_node[node]
                for left in range(DIMENSION):
                    right[left] += (
                        cross[left] * gradient_node[node] / denominator
                    )
                    for column in range(DIMENSION):
                        schur[left][column] -= (
                            cross[left] * cross[column] / denominator
                        )
            delta_weight = solve_float(schur, right)
        else:
            delta_weight = [0.0] * DIMENSION
        delta_node = {
            node: (
                -gradient_node[node]
                - sum(
                    cross * delta
                    for cross, delta in zip(cross_node[node], delta_weight)
                )
            )
            / diagonal_node[node]
            for node in intercepts
        }

        previous = objective(samples, target_name, intercepts, weights)
        accepted = False
        step = 1.0
        for _attempt in range(16):
            trial_intercepts = {
                node: intercepts[node] + step * delta_node[node]
                for node in intercepts
            }
            trial_weights = [
                weight + step * delta
                for weight, delta in zip(weights, delta_weight)
            ]
            current = objective(
                samples, target_name, trial_intercepts, trial_weights
            )
            if current <= previous:
                intercepts = trial_intercepts
                weights = trial_weights
                accepted = True
                break
            step *= 0.5
        if not accepted:
            break

    integer_intercepts = {
        node: max(
            -MAX_SCORE,
            min(MAX_SCORE, round(intercept / LOG_BASE)),
        )
        for node, intercept in intercepts.items()
    }
    integer_weights = [
        max(-2**31, min(2**31 - 1, round(weight / LOG_BASE)))
        for weight in weights
    ]
    return {
        "intercepts": integer_intercepts,
        "stateful": stateful,
        "target": target_name,
        "weights": integer_weights,
    }


def build_lookup() -> list[int]:
    positive = [0] * (MAX_SCORE + 1)
    numerator = 1
    denominator = 1
    for score in range(MAX_SCORE + 1):
        if score:
            numerator *= ODDS_NUMERATOR
            denominator *= ODDS_DENOMINATOR
        frequency = round_fraction(
            Fraction(TOTAL * numerator, numerator + denominator)
        )
        positive[score] = max(1, min(TOTAL - 1, frequency))
    table = [0] * (2 * MAX_SCORE + 1)
    for score, frequency in enumerate(positive):
        table[MAX_SCORE + score] = frequency
        table[MAX_SCORE - score] = TOTAL - frequency
    return table


LOOKUP = build_lookup()


def predict(model: dict[str, object], sample: dict[str, object]) -> int:
    intercepts = model["intercepts"]
    weights = model["weights"]
    node = sample["node"]
    features = sample["features"]
    assert isinstance(intercepts, dict)
    assert isinstance(weights, list)
    assert isinstance(node, tuple)
    assert isinstance(features, tuple)
    correction = round_div(
        sum(weight * feature for weight, feature in zip(weights, features)),
        HALF,
    )
    score = max(
        -MAX_SCORE,
        min(MAX_SCORE, int(intercepts.get(node, 0)) + correction),
    )
    return LOOKUP[MAX_SCORE + score]


def serialize(model: dict[str, object]) -> bytes:
    intercepts = model["intercepts"]
    weights = model["weights"]
    assert isinstance(intercepts, dict)
    assert isinstance(weights, list)
    output = bytearray(
        struct.pack(
            "<8sBHHHHH",
            MODEL_MAGIC,
            len(SHIFTS),
            TOTAL,
            ODDS_NUMERATOR,
            ODDS_DENOMINATOR,
            MAX_SCORE,
            len(intercepts),
        )
    )
    output.extend(bytes(SHIFTS))
    for weight in weights:
        output.extend(struct.pack("<i", weight))
    for frequency in LOOKUP:
        output.extend(struct.pack("<H", frequency))
    for node in sorted(intercepts):
        output.extend(struct.pack("<HHh", node[0], node[1], intercepts[node]))
    return bytes(output)


def model_result(
    name: str,
    model: dict[str, object],
    holdout: list[dict[str, object]],
    output_dir: Path,
) -> dict[str, object]:
    ideal_bits = sum(
        loss(predict(model, sample), int(sample["bit"])) for sample in holdout
    )
    raw = serialize(model)
    model_path = output_dir / f"{name}.bin"
    model_path.write_bytes(raw)
    packed = lzma.compress(
        raw, format=lzma.FORMAT_ALONE, preset=9 | lzma.PRESET_EXTREME
    )
    return {
        "ideal_bits": ideal_bits,
        "model_bytes": len(raw),
        "model_path": str(model_path),
        "model_sha256": sha256(raw),
        "packed_model_bytes": len(packed),
        "packed_model_sha256": sha256(packed),
        "two_part_proxy_bytes": math.ceil(ideal_bits / 8) + len(packed),
        "weight_l1": sum(abs(value) for value in model["weights"]),
        "weights": model["weights"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--train-rows", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    rows = load(args.trace)
    if not 0 < args.train_rows < len(rows):
        raise ValueError("invalid train-row split")
    samples = materialize_samples(rows)
    training = [sample for sample in samples if int(sample["row"]) < args.train_rows]
    holdout = [sample for sample in samples if int(sample["row"]) >= args.train_rows]
    args.output.parent.mkdir(parents=True, exist_ok=True)

    models = {
        "soft_static": fit(training, "teacher", False),
        "hard_static": fit(training, "hard", False),
        "soft_stateful": fit(training, "teacher", True),
        "hard_stateful": fit(training, "hard", True),
    }
    results = {
        name: model_result(name, model, holdout, args.output.parent)
        for name, model in models.items()
    }
    teacher_bits = sum(
        loss(int(sample["teacher"]), int(sample["bit"])) for sample in holdout
    )
    soft_state = results["soft_stateful"]
    hard_state = results["hard_stateful"]
    soft_static = results["soft_static"]
    teacher_value = (
        float(soft_state["ideal_bits"]) < float(hard_state["ideal_bits"])
        and int(soft_state["two_part_proxy_bytes"])
        < int(hard_state["two_part_proxy_bytes"])
    )
    recurrence_value = (
        float(soft_state["ideal_bits"]) < float(soft_static["ideal_bits"])
        and int(soft_state["two_part_proxy_bytes"])
        < int(soft_static["two_part_proxy_bytes"])
    )
    authorize = teacher_value and recurrence_value
    receipt = {
        "authorization": (
            "requires_mature_native_gate"
            if authorize
            else "terminal_startup_negative_for_logit_state"
        ),
        "claim_boundary": (
            "Chronological startup causal shadow with exact serialized "
            "rational-odds lookup and integer model. Ideal loss and two-part "
            "proxy are not native arithmetic bytes or Hutter score evidence."
        ),
        "holdout_branches": len(holdout),
        "holdout_rows": len(rows) - args.train_rows,
        "intercept_ridge": INTERCEPT_RIDGE,
        "lookup_entries": len(LOOKUP),
        "lookup_max_score": MAX_SCORE,
        "models": results,
        "newton_steps": NEWTON_STEPS,
        "odds_denominator": ODDS_DENOMINATOR,
        "odds_numerator": ODDS_NUMERATOR,
        "recurrence_value_positive": recurrence_value,
        "schema": "nncp_branch_logit_state_screen_v1",
        "score_credit_bytes": 0,
        "shifts": list(SHIFTS),
        "soft_stateful_minus_hard_stateful_bits": (
            float(soft_state["ideal_bits"]) - float(hard_state["ideal_bits"])
        ),
        "soft_stateful_minus_soft_static_bits": (
            float(soft_state["ideal_bits"]) - float(soft_static["ideal_bits"])
        ),
        "teacher_holdout_ideal_bits": teacher_bits,
        "teacher_value_positive": teacher_value,
        "trace_sha256": sha256(args.trace.read_bytes()),
        "train_branches": len(training),
        "train_rows": args.train_rows,
        "weight_ridge": WEIGHT_RIDGE,
    }
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "authorization": receipt["authorization"],
                "recurrence_value_positive": recurrence_value,
                "soft_stateful_minus_hard_stateful_bits": receipt[
                    "soft_stateful_minus_hard_stateful_bits"
                ],
                "soft_stateful_minus_soft_static_bits": receipt[
                    "soft_stateful_minus_soft_static_bits"
                ],
                "teacher_value_positive": teacher_value,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
