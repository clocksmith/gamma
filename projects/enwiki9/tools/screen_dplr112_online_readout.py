#!/usr/bin/env python3
"""Screen a cheap causal online prefix readout over continuous DPLR rollout."""

import argparse
import hashlib
import json
import math
import struct
import time
from pathlib import Path

import numpy as np

from train_dplr112_readout_shadow import TeacherTrace
from train_dplr112_state_shadow import StateTrace


def load_parameters(path):
    archive = np.load(path)
    result = {}
    for name in archive.files:
        if name.endswith(".scale"):
            continue
        result[name] = archive[name].astype(np.float32) * float(
            archive[name + ".scale"]
        )
    return result


def sigmoid(values):
    return 1.0 / (1.0 + np.exp(-np.clip(values, -30.0, 30.0)))


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-trace", required=True)
    parser.add_argument("--teacher-trace", required=True)
    parser.add_argument("--branch", choices=("main", "side"), required=True)
    parser.add_argument("--dplr-parameters", required=True)
    parser.add_argument("--learning-rates", default="0.0003,0.001,0.003,0.01,0.03")
    parser.add_argument("--holdout-fraction", type=float, default=0.2)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    trace = StateTrace(args.state_trace)
    teacher = TeacherTrace(args.teacher_trace, args.branch)
    parameters = load_parameters(args.dplr_parameters)
    rates = np.array(
        [float(value) for value in args.learning_rates.split(",")],
        dtype=np.float32,
    )
    models = len(rates)
    weights = np.zeros((models, 255, trace.cells), dtype=np.float32)
    bias = np.zeros((models, 255), dtype=np.float32)
    hidden = np.zeros(trace.cells, dtype=np.float32)
    cell = np.zeros(trace.cells, dtype=np.float32)
    total_student = np.zeros(models, dtype=np.float64)
    holdout_student = np.zeros(models, dtype=np.float64)
    total_teacher = 0.0
    holdout_teacher = 0.0
    holdout_start = int(trace.rows * (1.0 - args.holdout_fraction))
    started = time.monotonic()

    projection = parameters["projection"]
    expansion = parameters["expansion"]
    diagonal = parameters["diagonal"]
    event = parameters["event.weight"]
    event_expansion = parameters["event_expansion"]
    gate_bias = parameters["bias"]

    for index in range(trace.rows):
        features, symbol, _, _, _, _ = trace.take(np.array([index]))
        combined = np.concatenate((features[0], hidden))
        projected = projection @ combined
        gates = np.einsum("gcr,r->gc", expansion, projected)
        gates += diagonal * hidden[None, :]
        gates += np.einsum(
            "gce,e->gc", event_expansion, event[int(symbol[0])]
        )
        gates += gate_bias
        forget = sigmoid(gates[0])
        node_value = np.tanh(gates[1])
        output = sigmoid(gates[2])
        cell = forget * cell + (1.0 - forget) * node_value
        hidden = output * np.tanh(cell)

        target_probability, actual_bits, nodes = teacher.take_bytes(
            np.array([index + 1])
        )
        for position in range(8):
            node = int(nodes[0, position])
            bit = int(actual_bits[0, position])
            teacher_p = float(
                np.clip(target_probability[0, position], 1e-7, 1.0 - 1e-7)
            )
            prediction = sigmoid(weights[:, node, :] @ hidden + bias[:, node])
            prediction = np.clip(prediction, 1e-7, 1.0 - 1e-7)
            student_loss = -np.log2(
                prediction if bit else 1.0 - prediction
            )
            teacher_loss = -math.log2(teacher_p if bit else 1.0 - teacher_p)
            total_student += student_loss
            total_teacher += teacher_loss
            if index >= holdout_start:
                holdout_student += student_loss
                holdout_teacher += teacher_loss
            error = prediction - bit
            weights[:, node, :] -= (
                rates[:, None] * error[:, None] * hidden[None, :]
            )
            bias[:, node] -= rates * error
        if index == 0 or (index + 1) % 20000 == 0:
            print(
                json.dumps(
                    {
                        "rows": index + 1,
                        "elapsed_seconds": time.monotonic() - started,
                        "best_total_bits_per_byte": float(
                            np.min(total_student / (index + 1))
                        ),
                    }
                ),
                flush=True,
            )

    holdout_rows = trace.rows - holdout_start
    candidates = []
    for model_index, rate in enumerate(rates):
        candidates.append(
            {
                "learning_rate": float(rate),
                "total_student_bits": float(total_student[model_index]),
                "total_student_bits_per_byte": float(
                    total_student[model_index] / trace.rows
                ),
                "total_teacher_bits": total_teacher,
                "total_student_minus_teacher_bits": float(
                    total_student[model_index] - total_teacher
                ),
                "holdout_rows": holdout_rows,
                "holdout_student_bits": float(holdout_student[model_index]),
                "holdout_student_bits_per_byte": float(
                    holdout_student[model_index] / holdout_rows
                ),
                "holdout_teacher_bits": holdout_teacher,
                "holdout_student_minus_teacher_bits": float(
                    holdout_student[model_index] - holdout_teacher
                ),
            }
        )
    candidates.sort(key=lambda row: row["holdout_student_bits"])
    receipt = {
        "schema": "dplr112_online_prefix_readout_screen_v1",
        "configuration": vars(args),
        "inputs": {
            "state_trace_sha256": sha256(args.state_trace),
            "teacher_trace_sha256": sha256(args.teacher_trace),
            "dplr_parameters_sha256": sha256(args.dplr_parameters),
            "rows": trace.rows,
            "inputs": trace.inputs,
            "cells": trace.cells,
            "target_shift_bytes": 1,
        },
        "initialization": {
            "readout_weights": "all zero",
            "readout_bias": "all zero",
            "transmitted_readout_parameter_bytes": 0,
        },
        "candidates": candidates,
        "best": candidates[0],
        "runtime": {
            "elapsed_seconds": time.monotonic() - started,
        },
        "contract": {
            "continuous_student_state_from_zero": True,
            "causal_online_updates": True,
            "teacher_state_used_during_rollout": False,
            "integer_inference_implemented": False,
            "native_archive_evidence": False,
        },
    }
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"receipt": str(output), "best": candidates[0]}))


if __name__ == "__main__":
    main()
