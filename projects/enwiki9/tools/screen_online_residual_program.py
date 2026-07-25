#!/usr/bin/env python3
"""Screen a zero-package causal residual program against endpoint428 traces."""

import argparse
import hashlib
import json
import math
import struct
import time
from pathlib import Path

import numpy as np


HEADER = struct.Struct("<8sIIIIQ")
ROW = np.dtype(
    [
        ("base", "<u2"),
        ("side", "<u2"),
        ("main", "<u2"),
        ("final", "<u2"),
        ("bit", "u1"),
    ]
)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sigmoid(values):
    return 1.0 / (1.0 + np.exp(-np.clip(values, -30.0, 30.0)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--learning-rates", default="0.001,0.003,0.01,0.03,0.1"
    )
    parser.add_argument("--hash-bits", type=int, default=18)
    parser.add_argument("--holdout-fraction", type=float, default=0.2)
    args = parser.parse_args()

    path = Path(args.trace).resolve()
    with path.open("rb") as handle:
        magic, version, header, row_bytes, _, rows = HEADER.unpack(
            handle.read(HEADER.size)
        )
    if magic != b"DPLRTRC1" or version != 1 or row_bytes != 9 or rows % 8:
        raise ValueError("unsupported teacher trace")
    data = np.memmap(path, mode="r", dtype=ROW, offset=header, shape=(rows,))
    byte_rows = rows // 8
    rates = np.array(
        [float(value) for value in args.learning_rates.split(",")],
        dtype=np.float32,
    )
    models = len(rates)
    node_table = np.zeros((models, 255), dtype=np.float32)
    base_table = np.zeros((models, 8, 64), dtype=np.float32)
    previous_table = np.zeros((models, 256, 8, 16), dtype=np.float32)
    hash_table = np.zeros((models, 1 << args.hash_bits), dtype=np.float32)
    hash_mask = (1 << args.hash_bits) - 1
    total_student = np.zeros(models, dtype=np.float64)
    holdout_student = np.zeros(models, dtype=np.float64)
    base_total = final_total = 0.0
    base_holdout = final_holdout = 0.0
    holdout_start = int(byte_rows * (1.0 - args.holdout_fraction))
    previous_1 = previous_2 = 0
    started = time.monotonic()

    for byte_index in range(byte_rows):
        node = 0
        value = 0
        start = byte_index * 8
        for position in range(8):
            row = data[start + position]
            bit = int(row["bit"])
            value = (value << 1) | bit
            base_u16 = int(row["base"])
            base_probability = min(max(base_u16 / 65536.0, 1e-7), 1.0 - 1e-7)
            final_probability = min(
                max(int(row["final"]) / 65536.0, 1e-7), 1.0 - 1e-7
            )
            base_logit = math.log(base_probability / (1.0 - base_probability))
            base_bin_64 = min(base_u16 >> 10, 63)
            base_bin_16 = min(base_u16 >> 12, 15)
            context_hash = (
                (previous_2 * 0x9E3779B1)
                ^ (previous_1 * 0x85EBCA77)
                ^ (node * 0xC2B2AE3D)
                ^ (base_bin_64 * 0x27D4EB2F)
                ^ (position * 0x165667B1)
            ) & hash_mask
            residual = (
                node_table[:, node]
                + base_table[:, position, base_bin_64]
                + previous_table[:, previous_1, position, base_bin_16]
                + hash_table[:, context_hash]
            )
            prediction = np.clip(sigmoid(base_logit + residual), 1e-7, 1.0 - 1e-7)
            student_loss = -np.log2(prediction if bit else 1.0 - prediction)
            base_loss = -math.log2(
                base_probability if bit else 1.0 - base_probability
            )
            final_loss = -math.log2(
                final_probability if bit else 1.0 - final_probability
            )
            total_student += student_loss
            base_total += base_loss
            final_total += final_loss
            if byte_index >= holdout_start:
                holdout_student += student_loss
                base_holdout += base_loss
                final_holdout += final_loss
            error = prediction - bit
            update = rates * error * 0.25
            node_table[:, node] -= update
            base_table[:, position, base_bin_64] -= update
            previous_table[:, previous_1, position, base_bin_16] -= update
            hash_table[:, context_hash] -= update
            node = 2 * node + 1 + bit
        previous_2, previous_1 = previous_1, value
        if byte_index == 0 or (byte_index + 1) % 100000 == 0:
            print(
                json.dumps(
                    {
                        "bytes": byte_index + 1,
                        "elapsed_seconds": time.monotonic() - started,
                        "best_bits_per_byte": float(
                            np.min(total_student / (byte_index + 1))
                        ),
                    }
                ),
                flush=True,
            )

    holdout_bytes = byte_rows - holdout_start
    candidates = []
    for model_index, rate in enumerate(rates):
        candidates.append(
            {
                "learning_rate": float(rate),
                "total_bits": float(total_student[model_index]),
                "total_bits_per_byte": float(total_student[model_index] / byte_rows),
                "total_delta_vs_base_bits": float(
                    total_student[model_index] - base_total
                ),
                "total_delta_vs_final_bits": float(
                    total_student[model_index] - final_total
                ),
                "holdout_bytes": holdout_bytes,
                "holdout_bits": float(holdout_student[model_index]),
                "holdout_bits_per_byte": float(
                    holdout_student[model_index] / holdout_bytes
                ),
                "holdout_delta_vs_base_bits": float(
                    holdout_student[model_index] - base_holdout
                ),
                "holdout_delta_vs_final_bits": float(
                    holdout_student[model_index] - final_holdout
                ),
            }
        )
    candidates.sort(key=lambda row: row["holdout_bits"])
    receipt = {
        "schema": "online_residual_program_screen_v1",
        "configuration": vars(args),
        "trace": {
            "path": str(path),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "coded_bytes": byte_rows,
        },
        "baselines": {
            "base_total_bits": base_total,
            "base_total_bits_per_byte": base_total / byte_rows,
            "final_total_bits": final_total,
            "final_total_bits_per_byte": final_total / byte_rows,
            "base_holdout_bits": base_holdout,
            "base_holdout_bits_per_byte": base_holdout / holdout_bytes,
            "final_holdout_bits": final_holdout,
            "final_holdout_bits_per_byte": final_holdout / holdout_bytes,
        },
        "candidates": candidates,
        "best": candidates[0],
        "resource_model": {
            "transmitted_parameter_bytes": 0,
            "adaptive_float_cells": int(
                255 + 8 * 64 + 256 * 8 * 16 + (1 << args.hash_bits)
            ),
            "table_lookups_per_bit": 4,
            "table_updates_per_bit": 4,
        },
        "runtime": {"elapsed_seconds": time.monotonic() - started},
        "contract": {
            "causal": True,
            "online_updates_use_only_decoded_bit": True,
            "teacher_probability_used_only_for_evaluation": True,
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
