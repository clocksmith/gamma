#!/usr/bin/env python3
"""Screen one frozen recurrent affine student on an exact NNCP branch trace."""

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

from nncp_branch_centroid_screen import TOTAL, load, loss


HALF = TOTAL // 2
SHIFTS = (2, 5, 9, 13)
DIMENSION = 2 * len(SHIFTS)
WEIGHT_SCALE = 1 << 20
WEIGHT_RIDGE = 1 << 30
INTERCEPT_RIDGE = 8
MODEL_MAGIC = b"NNAFS1\0\0"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def round_fraction(value: Fraction) -> int:
    sign = -1 if value < 0 else 1
    value = abs(value)
    quotient, remainder = divmod(value.numerator, value.denominator)
    if 2 * remainder >= value.denominator:
        quotient += 1
    return sign * quotient


def round_div(numerator: int, denominator: int) -> int:
    return round_fraction(Fraction(numerator, denominator))


def update(value: int, target: int, shift: int) -> int:
    result = value + round_div(target - value, 1 << shift)
    return max(0, min(TOTAL, result))


def solve(matrix: list[list[Fraction]], vector: list[Fraction]) -> list[Fraction]:
    size = len(vector)
    augmented = [row[:] + [vector[index]] for index, row in enumerate(matrix)]
    for column in range(size):
        pivot = next(
            row for row in range(column, size) if augmented[row][column] != 0
        )
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


def materialize_samples(
    rows: list[tuple[int, list[tuple[int, int, int, int]]]],
) -> list[dict[str, object]]:
    node_states: dict[tuple[int, int], list[int]] = {}
    global_state = [HALF] * len(SHIFTS)
    samples: list[dict[str, object]] = []
    for row_index, (_symbol, branches) in enumerate(rows):
        for start, active, teacher, bit in branches:
            node = (start, active)
            local = node_states.setdefault(node, [HALF] * len(SHIFTS))
            features = tuple(
                value - HALF for value in (*local, *global_state)
            )
            samples.append(
                {
                    "bit": bit,
                    "features": features,
                    "hard": TOTAL if bit == 0 else 0,
                    "node": node,
                    "row": row_index,
                    "teacher": teacher,
                }
            )
            target = TOTAL if bit == 0 else 0
            for index, shift in enumerate(SHIFTS):
                local[index] = update(local[index], target, shift)
                global_state[index] = update(global_state[index], target, shift)
    return samples


def sufficient_statistics(
    samples: list[dict[str, object]], target_name: str
) -> tuple[
    list[list[int]],
    list[int],
    dict[tuple[int, int], tuple[int, list[int], int]],
]:
    xx = [[0] * DIMENSION for _ in range(DIMENSION)]
    xy = [0] * DIMENSION
    counts: dict[tuple[int, int], int] = defaultdict(int)
    sums_x: dict[tuple[int, int], list[int]] = defaultdict(
        lambda: [0] * DIMENSION
    )
    sums_y: dict[tuple[int, int], int] = defaultdict(int)
    for sample in samples:
        node = sample["node"]
        features = sample["features"]
        target = int(sample[target_name]) - HALF
        assert isinstance(node, tuple)
        assert isinstance(features, tuple)
        counts[node] += 1
        sums_y[node] += target
        for i, left in enumerate(features):
            sums_x[node][i] += left
            xy[i] += left * target
            for j, right in enumerate(features):
                xx[i][j] += left * right
    nodes = {
        node: (counts[node], sums_x[node], sums_y[node]) for node in counts
    }
    return xx, xy, nodes


def fit(
    samples: list[dict[str, object]], target_name: str, stateful: bool
) -> dict[str, object]:
    xx, xy, nodes = sufficient_statistics(samples, target_name)
    if stateful:
        matrix = [
            [
                Fraction(xx[i][j] + (WEIGHT_RIDGE if i == j else 0))
                for j in range(DIMENSION)
            ]
            for i in range(DIMENSION)
        ]
        vector = [Fraction(value) for value in xy]
        for count, sums_x, sum_y in nodes.values():
            denominator = count + INTERCEPT_RIDGE
            for i in range(DIMENSION):
                vector[i] -= Fraction(sums_x[i] * sum_y, denominator)
                for j in range(DIMENSION):
                    matrix[i][j] -= Fraction(
                        sums_x[i] * sums_x[j], denominator
                    )
        beta = solve(matrix, vector)
    else:
        beta = [Fraction(0)] * DIMENSION

    weights = [round_fraction(value * WEIGHT_SCALE) for value in beta]
    intercepts: dict[tuple[int, int], int] = {}
    for node, (count, sums_x, sum_y) in nodes.items():
        residual = Fraction(sum_y) - sum(
            coefficient * feature
            for coefficient, feature in zip(beta, sums_x)
        )
        centered = residual / (count + INTERCEPT_RIDGE)
        intercepts[node] = max(
            1, min(TOTAL - 1, HALF + round_fraction(centered))
        )
    return {
        "intercepts": intercepts,
        "stateful": stateful,
        "target": target_name,
        "weights": weights,
    }


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
        WEIGHT_SCALE,
    )
    return max(1, min(TOTAL - 1, int(intercepts.get(node, HALF)) + correction))


def serialize(model: dict[str, object]) -> bytes:
    intercepts = model["intercepts"]
    weights = model["weights"]
    assert isinstance(intercepts, dict)
    assert isinstance(weights, list)
    output = bytearray(
        struct.pack(
            "<8sBIIH",
            MODEL_MAGIC,
            len(SHIFTS),
            WEIGHT_SCALE,
            INTERCEPT_RIDGE,
            len(intercepts),
        )
    )
    output.extend(bytes(SHIFTS))
    for weight in weights:
        output.extend(struct.pack("<q", weight))
    for node in sorted(intercepts):
        output.extend(struct.pack("<HHH", node[0], node[1], intercepts[node]))
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

    models = {
        "soft_static": fit(training, "teacher", False),
        "hard_static": fit(training, "hard", False),
        "soft_stateful": fit(training, "teacher", True),
        "hard_stateful": fit(training, "hard", True),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
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
            else "terminal_startup_negative_for_affine_state"
        ),
        "claim_boundary": (
            "Chronological startup causal shadow with exact integer student "
            "state and frequencies. Ideal loss and two-part proxy are not "
            "native arithmetic bytes or Hutter score evidence."
        ),
        "holdout_branches": len(holdout),
        "holdout_rows": len(rows) - args.train_rows,
        "intercept_ridge": INTERCEPT_RIDGE,
        "models": results,
        "recurrence_value_positive": recurrence_value,
        "schema": "nncp_branch_affine_state_screen_v1",
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
        "weight_scale": WEIGHT_SCALE,
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
