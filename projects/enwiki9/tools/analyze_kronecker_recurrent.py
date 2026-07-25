#!/usr/bin/env python3
"""Measure structured approximation spectra of exact endpoint428 weights."""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

import numpy as np


def retained_energy(matrix, ranks):
    singular = np.linalg.svd(matrix.astype(np.float64), compute_uv=False)
    energy = np.square(singular)
    total = float(energy.sum())
    return {
        str(rank): float(energy[:rank].sum() / total)
        for rank in ranks
        if rank <= len(singular)
    }


def kronecker_spectrum(matrix, outer, inner, ranks):
    rearranged = (
        matrix.reshape(outer, inner, outer, inner)
        .transpose(0, 2, 1, 3)
        .reshape(outer * outer, inner * inner)
    )
    return retained_energy(rearranged, ranks)


def analyze(path):
    with path.open("rb") as handle:
        header = handle.read(28)
        magic, version, inputs, outputs, cells, layers = struct.unpack(
            "<8s5I", header
        )
        values = np.fromfile(handle, dtype="<f4")
    if magic != b"DPLRWGT1" or version != 1 or cells != 112:
        raise ValueError("unsupported weight snapshot")
    cursor = outputs * (cells * layers + 1)
    result = {
        "path": str(path),
        "inputs": inputs,
        "outputs": outputs,
        "cells": cells,
        "layers": layers,
        "output_matrix_floats": cursor,
        "gates": [],
    }
    names = ("forget", "input_node", "output")
    for layer in range(layers):
        vector_size = 1 + cells + inputs if layer == 0 else inputs + 1 + 2 * cells
        columns = outputs + vector_size
        for gate in names:
            count = cells * columns
            matrix = values[cursor : cursor + count].reshape(cells, columns)
            cursor += count
            categorical = matrix[:, :outputs]
            external = matrix[:, outputs : outputs + inputs]
            own_start = outputs + inputs
            own_hidden = matrix[:, own_start : own_start + cells]
            item = {
                "layer": layer,
                "gate": gate,
                "columns": columns,
                "categorical_low_rank_energy": retained_energy(
                    categorical, (1, 2, 4, 8, 16, 32, 64)
                ),
                "external_low_rank_energy": retained_energy(
                    external, (1, 2, 4, 8, 16, 32, 64)
                ),
                "own_hidden_low_rank_energy": retained_energy(
                    own_hidden, (1, 2, 4, 8, 16, 32, 64)
                ),
                "own_hidden_kronecker_energy": kronecker_spectrum(
                    own_hidden, 7, 16, (1, 2, 4, 8, 16, 32, 49)
                ),
            }
            if layer:
                lower_start = own_start + cells
                lower_hidden = matrix[:, lower_start : lower_start + cells]
                item["lower_hidden_low_rank_energy"] = retained_energy(
                    lower_hidden, (1, 2, 4, 8, 16, 32, 64)
                )
                item["lower_hidden_kronecker_energy"] = kronecker_spectrum(
                    lower_hidden, 7, 16, (1, 2, 4, 8, 16, 32, 49)
                )
            result["gates"].append(item)
    if cursor != len(values):
        raise ValueError(
            f"weight parse mismatch: consumed {cursor}, found {len(values)}"
        )
    result["snapshot_floats"] = len(values)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", type=Path, required=True)
    parser.add_argument("--side", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = {
        "schema": "endpoint428_kronecker_spectrum_v1",
        "main": analyze(args.main),
        "side": analyze(args.side),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
