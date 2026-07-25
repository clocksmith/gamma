#!/usr/bin/env python3
"""Compile endpoint428's final-minus-base trace into counted hashed offsets."""

import argparse
import hashlib
import json
import struct
import time
import zlib
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


def sigmoid(value):
    return 1.0 / (1.0 + np.exp(-np.clip(value, -30.0, 30.0)))


def coding_bits(probability, bit):
    probability = np.clip(probability, 1e-7, 1.0 - 1e-7)
    return float(
        np.sum(
            -(
                bit * np.log2(probability)
                + (1.0 - bit) * np.log2(1.0 - probability)
            )
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--table-bits", default="12,14,16,17")
    parser.add_argument("--regularization", default="1,4,16")
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--train-fraction", type=float, default=0.8)
    parser.add_argument("--projection-scale", type=float, default=1000.0)
    args = parser.parse_args()

    path = Path(args.trace).resolve()
    with path.open("rb") as handle:
        magic, version, header, row_bytes, _, rows = HEADER.unpack(
            handle.read(HEADER.size)
        )
    if magic != b"DPLRTRC1" or version != 1 or row_bytes != 9 or rows % 8:
        raise ValueError("unsupported trace")
    trace = np.memmap(path, mode="r", dtype=ROW, offset=header, shape=(rows,))
    bits = np.asarray(trace["bit"], dtype=np.uint8)
    bit_matrix = bits.reshape(-1, 8)
    byte_values = np.packbits(bit_matrix, axis=1, bitorder="big").ravel()
    byte_count = len(byte_values)
    previous_1 = np.zeros(byte_count, dtype=np.uint64)
    previous_2 = np.zeros(byte_count, dtype=np.uint64)
    previous_1[1:] = byte_values[:-1]
    previous_2[2:] = byte_values[:-2]
    previous_1 = np.repeat(previous_1, 8)
    previous_2 = np.repeat(previous_2, 8)
    positions = np.tile(np.arange(8, dtype=np.uint64), byte_count)
    nodes = np.empty_like(bit_matrix, dtype=np.uint64)
    prefix = np.zeros(byte_count, dtype=np.uint64)
    for position in range(8):
        nodes[:, position] = prefix
        prefix = 2 * prefix + 1 + bit_matrix[:, position]
    nodes = nodes.ravel()
    base_u16 = np.asarray(trace["base"], dtype=np.uint64)
    base_probability = np.clip(base_u16.astype(np.float64) / 65536.0, 1e-7, 1 - 1e-7)
    final_probability = np.clip(
        np.asarray(trace["final"], dtype=np.float64) / 65536.0, 1e-7, 1 - 1e-7
    )
    base_logit = np.log(base_probability / (1.0 - base_probability))
    base_bin = base_u16 >> 10
    mixed_hash = (
        previous_2 * np.uint64(0x9E3779B185EBCA87)
        ^ previous_1 * np.uint64(0xC2B2AE3D27D4EB4F)
        ^ nodes * np.uint64(0x165667B19E3779F9)
        ^ base_bin * np.uint64(0x85EBCA77C2B2AE63)
        ^ positions * np.uint64(0x27D4EB2F165667C5)
    )
    split = int(rows * args.train_fraction) // 8 * 8
    train = slice(0, split)
    holdout = slice(split, rows)
    base_total_bits = coding_bits(base_probability, bits)
    final_total_bits = coding_bits(final_probability, bits)
    base_holdout_bits = coding_bits(base_probability[holdout], bits[holdout])
    final_holdout_bits = coding_bits(final_probability[holdout], bits[holdout])
    candidates = []
    started = time.monotonic()

    for table_bits in [int(value) for value in args.table_bits.split(",")]:
        cells = 1 << table_bits
        keys = np.asarray(mixed_hash & np.uint64(cells - 1), dtype=np.int64)
        train_keys = keys[train]
        for regularization in [
            float(value) for value in args.regularization.split(",")
        ]:
            offset = np.zeros(cells, dtype=np.float64)
            for _ in range(args.iterations):
                prediction = sigmoid(base_logit[train] + offset[train_keys])
                gradient = np.bincount(
                    train_keys,
                    weights=prediction - final_probability[train],
                    minlength=cells,
                )
                curvature = np.bincount(
                    train_keys,
                    weights=prediction * (1.0 - prediction),
                    minlength=cells,
                )
                offset -= gradient / (curvature + regularization)
            scale = max(float(np.max(np.abs(offset))) / 127.0, 1e-12)
            quantized = np.clip(np.rint(offset / scale), -127, 127).astype(np.int8)
            restored = quantized.astype(np.float64) * scale
            student_probability = sigmoid(base_logit + restored[keys])
            total_bits = coding_bits(student_probability, bits)
            holdout_bits = coding_bits(
                student_probability[holdout], bits[holdout]
            )
            package = zlib.compress(
                quantized.tobytes() + struct.pack("<f", scale), level=9
            )
            package_bytes = len(package)
            projected_archive_savings_bytes = (
                (base_total_bits - total_bits) / 8.0 * args.projection_scale
            )
            projected_net_savings_bytes = (
                projected_archive_savings_bytes - package_bytes
            )
            candidates.append(
                {
                    "table_bits": table_bits,
                    "cells": cells,
                    "regularization": regularization,
                    "scale": scale,
                    "raw_parameter_bytes": cells + 4,
                    "zlib_parameter_bytes": package_bytes,
                    "total_bits": total_bits,
                    "total_bits_per_byte": total_bits / byte_count,
                    "total_delta_vs_base_bits": total_bits - base_total_bits,
                    "total_delta_vs_final_bits": total_bits - final_total_bits,
                    "holdout_bits": holdout_bits,
                    "holdout_bits_per_byte": holdout_bits / (byte_count - split // 8),
                    "holdout_delta_vs_base_bits": holdout_bits
                    - base_holdout_bits,
                    "holdout_delta_vs_final_bits": holdout_bits
                    - final_holdout_bits,
                    "projected_archive_savings_bytes": projected_archive_savings_bytes,
                    "projected_net_savings_bytes": projected_net_savings_bytes,
                }
            )
            print(json.dumps(candidates[-1]), flush=True)

    candidates.sort(
        key=lambda candidate: (
            -candidate["projected_net_savings_bytes"],
            candidate["holdout_bits"],
        )
    )
    receipt = {
        "schema": "hashed_residual_program_compiler_v1",
        "configuration": vars(args),
        "trace": {
            "path": str(path),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "coded_bytes": byte_count,
        },
        "split": {"train_rows": split, "holdout_rows": rows - split},
        "baselines": {
            "base_total_bits": base_total_bits,
            "final_total_bits": final_total_bits,
            "base_holdout_bits": base_holdout_bits,
            "final_holdout_bits": final_holdout_bits,
        },
        "candidates": candidates,
        "best": candidates[0],
        "runtime": {"elapsed_seconds": time.monotonic() - started},
        "contract": {
            "causal_features": True,
            "sealed_holdout_not_used_for_fitting": True,
            "parameter_bytes_counted": True,
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
