#!/usr/bin/env python3
"""Measure row-wise binary and low-bit quantization of endpoint428 weights."""

from __future__ import annotations

import argparse
import json
import math
import struct
from pathlib import Path

import numpy as np


def quantize_binary(matrix):
    scale = np.mean(np.abs(matrix), axis=1, keepdims=True)
    quantized = np.where(matrix >= 0.0, scale, -scale)
    return quantized


def quantize_ternary(matrix):
    result = np.empty_like(matrix)
    absolute = np.abs(matrix)
    mean = np.mean(absolute, axis=1, keepdims=True)
    for row in range(len(matrix)):
        best_error = float("inf")
        best = None
        for factor in np.linspace(0.2, 1.6, 29):
            mask = absolute[row] >= factor * mean[row, 0]
            if not np.any(mask):
                continue
            scale = float(absolute[row, mask].mean())
            candidate = np.zeros_like(matrix[row])
            candidate[mask] = np.sign(matrix[row, mask]) * scale
            error = float(np.square(matrix[row] - candidate).sum())
            if error < best_error:
                best_error = error
                best = candidate
        result[row] = best
    return result


def quantize_symmetric(matrix, maximum_level):
    result = np.empty_like(matrix)
    absolute_max = np.max(np.abs(matrix), axis=1)
    for row in range(len(matrix)):
        best_error = float("inf")
        best = None
        base = absolute_max[row] / maximum_level
        for factor in np.linspace(0.5, 1.5, 41):
            scale = base * factor if base else 1.0
            levels = np.clip(
                np.rint(matrix[row] / scale), -maximum_level, maximum_level
            )
            candidate = levels * scale
            error = float(np.square(matrix[row] - candidate).sum())
            if error < best_error:
                best_error = error
                best = candidate
        result[row] = best
    return result


def metrics(matrix, quantized, bits):
    energy = float(np.square(matrix.astype(np.float64)).sum())
    error = float(
        np.square(matrix.astype(np.float64) - quantized.astype(np.float64)).sum()
    )
    rows, columns = matrix.shape
    return {
        "rows": rows,
        "columns": columns,
        "retained_energy": 1.0 - error / energy,
        "packed_weight_bytes": math.ceil(rows * columns * bits / 8),
        "fp16_row_scale_bytes": rows * 2,
    }


def analyze_matrix(name, matrix):
    return {
        "name": name,
        "binary": metrics(matrix, quantize_binary(matrix), 1),
        "ternary": metrics(matrix, quantize_ternary(matrix), 2),
        "int4": metrics(matrix, quantize_symmetric(matrix, 7), 4),
    }


def analyze(path):
    with path.open("rb") as handle:
        header = handle.read(28)
        magic, version, inputs, outputs, cells, layers = struct.unpack(
            "<8s5I", header
        )
        values = np.fromfile(handle, dtype="<f4")
    if magic != b"DPLRWGT1" or version != 1:
        raise ValueError("unsupported snapshot")
    cursor = 0
    matrices = []
    output_columns = cells * layers + 1
    count = outputs * output_columns
    matrices.append(
        analyze_matrix(
            "output", values[cursor : cursor + count].reshape(outputs, output_columns)
        )
    )
    cursor += count
    for layer in range(layers):
        vector_size = 1 + cells + inputs if layer == 0 else inputs + 1 + 2 * cells
        columns = outputs + vector_size
        for gate in ("forget", "input_node", "output_gate"):
            count = cells * columns
            matrices.append(
                analyze_matrix(
                    f"layer{layer}.{gate}",
                    values[cursor : cursor + count].reshape(cells, columns),
                )
            )
            cursor += count
    if cursor != len(values):
        raise ValueError("weight parse mismatch")
    totals = {}
    for method in ("binary", "ternary", "int4"):
        packed = sum(item[method]["packed_weight_bytes"] for item in matrices)
        scales = sum(item[method]["fp16_row_scale_bytes"] for item in matrices)
        totals[method] = {
            "packed_weight_bytes": packed,
            "fp16_row_scale_bytes": scales,
            "total_parameter_bytes": packed + scales,
        }
    return {
        "path": str(path),
        "float_weights": len(values),
        "matrices": matrices,
        "totals": totals,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", type=Path, required=True)
    parser.add_argument("--side", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    main_result = analyze(args.main)
    side_result = analyze(args.side)
    combined = {}
    for method in ("binary", "ternary", "int4"):
        combined[method] = {
            key: main_result["totals"][method][key]
            + side_result["totals"][method][key]
            for key in (
                "packed_weight_bytes",
                "fp16_row_scale_bytes",
                "total_parameter_bytes",
            )
        }
    receipt = {
        "schema": "endpoint428_binary_weight_quantization_v1",
        "main": main_result,
        "side": side_result,
        "combined": combined,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
