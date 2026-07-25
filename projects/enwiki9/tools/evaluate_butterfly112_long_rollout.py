#!/usr/bin/env python3
"""Evaluate a fixed butterfly codec state without periodic teacher resets."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import torch
from torch import nn

from train_butterfly112_readout_shadow import (
    load_teacher_bytes,
    prefix_tables,
    quantized_readout_state,
    readout_logits,
)
from train_butterfly112_state_shadow import ButterflyLstm, Trace, fake_int8


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--teacher-trace", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--readout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--input-rank", type=int, required=True)
    parser.add_argument("--event-rank", type=int, required=True)
    parser.add_argument("--rows", type=int, default=120000)
    parser.add_argument("--holdout-start", type=int, default=102000)
    parser.add_argument("--reset-interval", type=int, default=0)
    parser.add_argument("--threads", type=int, default=1)
    args = parser.parse_args()

    torch.set_num_threads(args.threads)
    device = torch.device("cpu")
    trace = Trace(args.trace)
    teacher_bytes = load_teacher_bytes(args.teacher_trace)
    if (
        trace.rows < args.rows
        or len(teacher_bytes) <= args.rows
        or args.holdout_start >= args.rows
    ):
        raise ValueError("insufficient aligned rows")

    model = ButterflyLstm(
        trace.inputs, trace.cells, args.input_rank, args.event_rank
    ).to(device)
    model.load_state_dict(
        torch.load(args.model, map_location=device, weights_only=True)
    )
    model.load_state_dict(fake_int8(model))
    model.eval()
    readout = nn.Linear(trace.cells, 255, bias=True).to(device)
    readout.load_state_dict(
        torch.load(args.readout, map_location=device, weights_only=True)
    )
    readout.load_state_dict(quantized_readout_state(readout))
    readout.eval()
    nodes, bits = prefix_tables(device)

    raw = trace.data[: args.rows]
    x = torch.from_numpy(
        np.asarray(raw[:, 1 : trace.inputs + 1]).copy()
    ).to(device)
    event_values = np.asarray(raw[:, 0]).copy().view("<u4")
    event = torch.from_numpy(event_values.astype(np.int64)).to(device)
    first = trace.batch(np.asarray([0]), device)
    hidden = first[2]
    cell = first[3]
    if args.reset_interval:
        hidden = torch.zeros_like(hidden)
        cell = torch.zeros_like(cell)
    total_bits = 0.0
    with torch.no_grad():
        for index in range(args.rows):
            if args.reset_interval and index % args.reset_interval == 0:
                hidden.zero_()
                cell.zero_()
            hidden, cell = model(
                x[index : index + 1], event[index : index + 1], hidden, cell
            )
            if index >= args.holdout_start:
                target = torch.tensor(
                    [int(teacher_bytes[index + 1])],
                    dtype=torch.long,
                    device=device,
                )
                logits = readout_logits(readout, hidden, target, nodes)
                truth = bits.index_select(0, target)
                loss = nn.functional.binary_cross_entropy_with_logits(
                    logits, truth, reduction="sum"
                )
                total_bits += float(loss) / math.log(2.0)
            if (index + 1) % 10000 == 0:
                print(json.dumps({"rollout_rows": index + 1}), flush=True)

    holdout_rows = args.rows - args.holdout_start
    receipt = {
        "schema": "butterfly112_long_rollout_v1",
        "configuration": {
            key: str(value) if isinstance(value, Path) else value
            for key, value in vars(args).items()
        },
        "fake_int8_holdout": {
            "bytes": holdout_rows,
            "bits": total_bits,
            "bits_per_byte": total_bits / holdout_rows,
        },
        "contract": {
            "student_state_carried_from_row_zero": True,
            "no_teacher_reset_inside_rollout": True,
            "deterministic_zero_reset_interval": args.reset_interval,
            "one_byte_shifted_teacher_truth": True,
            "integer_inference_implemented": False,
            "native_archive_evidence": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
