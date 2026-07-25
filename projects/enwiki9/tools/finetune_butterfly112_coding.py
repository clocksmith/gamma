#!/usr/bin/env python3
"""Jointly fine-tune butterfly state and prefix readout on causal windows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn

from train_butterfly112_readout_shadow import (
    bit_cost,
    load_teacher_bytes,
    prefix_tables,
    quantized_readout_state,
    readout_logits,
)
from train_butterfly112_state_shadow import ButterflyLstm, Trace, fake_int8


@torch.no_grad()
def rollout_rate(
    model,
    readout,
    trace,
    teacher_bytes,
    start,
    rows,
    nodes,
    bits,
    device,
    reset_interval,
):
    first = trace.batch(np.asarray([start]), device)
    hidden = first[2]
    cell = first[3]
    if reset_interval:
        hidden = torch.zeros_like(hidden)
        cell = torch.zeros_like(cell)
    total = 0.0
    for index in range(start, start + rows):
        if reset_interval and (index - start) % reset_interval == 0:
            hidden.zero_()
            cell.zero_()
        batch = trace.batch(np.asarray([index]), device)
        hidden, cell = model(batch[0], batch[1], hidden, cell)
        target = torch.from_numpy(
            np.asarray(teacher_bytes[index + 1 : index + 2], dtype=np.int64)
        ).to(device)
        total += bit_cost(readout, hidden, target, nodes, bits)
    return {"bytes": rows, "bits": total, "bits_per_byte": total / rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--teacher-trace", type=Path, required=True)
    parser.add_argument("--input-model", type=Path, required=True)
    parser.add_argument("--input-readout", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--input-rank", type=int, required=True)
    parser.add_argument("--event-rank", type=int, required=True)
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--window", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--state-weight", type=float, default=0.5)
    parser.add_argument("--cell-weight", type=float, default=0.25)
    parser.add_argument("--rollout-rows", type=int, default=4096)
    parser.add_argument("--train-end", type=int, default=84000)
    parser.add_argument("--evaluation-start", type=int, default=102000)
    parser.add_argument("--zero-initial-state", action="store_true")
    parser.add_argument("--threads", type=int, default=6)
    parser.add_argument("--seed", type=int, default=112)
    args = parser.parse_args()

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(args.threads)
    device = torch.device("cpu")
    trace = Trace(args.trace)
    teacher_bytes = load_teacher_bytes(args.teacher_trace)
    split = args.train_end
    if (
        split <= args.window
        or split > trace.rows
        or len(teacher_bytes) <= split + args.window
        or args.evaluation_start + args.rollout_rows >= trace.rows
    ):
        raise ValueError("insufficient aligned trace rows")
    node_table, bit_table = prefix_tables(device)

    model = ButterflyLstm(
        trace.inputs, trace.cells, args.input_rank, args.event_rank
    ).to(device)
    model.load_state_dict(
        torch.load(args.input_model, map_location=device, weights_only=True)
    )
    readout = nn.Linear(trace.cells, 255, bias=True).to(device)
    readout.load_state_dict(
        torch.load(args.input_readout, map_location=device, weights_only=True)
    )
    optimizer = torch.optim.AdamW(
        list(model.parameters()) + list(readout.parameters()),
        lr=args.learning_rate,
    )
    rng = np.random.default_rng(args.seed)

    model.train()
    readout.train()
    last = None
    for step in range(args.steps):
        starts = rng.integers(
            0, split - args.window, size=args.batch_size, dtype=np.int64
        )
        indices = starts[:, None] + np.arange(args.window)[None, :]
        flat_indices = indices.reshape(-1)
        flat = trace.batch(flat_indices, device)
        shaped = [
            value.reshape(args.batch_size, args.window, -1) for value in flat
        ]
        x, event, hidden0, cell0, target_hidden, target_cell = shaped
        event = event.reshape(args.batch_size, args.window)
        target_values = np.asarray(
            teacher_bytes[flat_indices + 1], dtype=np.int64
        ).reshape(args.batch_size, args.window)
        targets = torch.from_numpy(target_values).to(device)
        hidden = hidden0[:, 0]
        cell = cell0[:, 0]
        if args.zero_initial_state:
            hidden = torch.zeros_like(hidden)
            cell = torch.zeros_like(cell)
        coding_loss = torch.zeros((), device=device)
        hidden_loss = torch.zeros((), device=device)
        cell_loss = torch.zeros((), device=device)
        for offset in range(args.window):
            hidden, cell = model(
                x[:, offset], event[:, offset], hidden, cell
            )
            target = targets[:, offset]
            logits = readout_logits(readout, hidden, target, node_table)
            truth = bit_table.index_select(0, target)
            coding_loss = coding_loss + nn.functional.binary_cross_entropy_with_logits(
                logits, truth
            )
            hidden_loss = hidden_loss + torch.mean(
                torch.square(hidden - target_hidden[:, offset])
            )
            cell_loss = cell_loss + torch.mean(
                torch.square(cell - target_cell[:, offset])
            )
        coding_loss = coding_loss / args.window
        state_loss = (
            hidden_loss + args.cell_weight * cell_loss
        ) / args.window
        loss = coding_loss + args.state_weight * state_loss
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            list(model.parameters()) + list(readout.parameters()), 5.0
        )
        optimizer.step()
        last = {
            "loss": float(loss.detach()),
            "coding_loss": float(coding_loss.detach()),
            "state_loss": float(state_loss.detach()),
        }
        if (step + 1) % 100 == 0:
            print(json.dumps({"step": step + 1} | last), flush=True)

    model.eval()
    readout.eval()
    start = args.evaluation_start
    float_rate = rollout_rate(
        model,
        readout,
        trace,
        teacher_bytes,
        start,
        args.rollout_rows,
        node_table,
        bit_table,
        device,
        args.window if args.zero_initial_state else 0,
    )
    float_model = {
        name: value.clone() for name, value in model.state_dict().items()
    }
    float_readout = {
        name: value.clone() for name, value in readout.state_dict().items()
    }
    model.load_state_dict(fake_int8(model))
    readout.load_state_dict(quantized_readout_state(readout))
    int8_rate = rollout_rate(
        model,
        readout,
        trace,
        teacher_bytes,
        start,
        args.rollout_rows,
        node_table,
        bit_table,
        device,
        args.window if args.zero_initial_state else 0,
    )
    model.load_state_dict(float_model)
    readout.load_state_dict(float_readout)
    model_parameters = sum(value.numel() for value in model.parameters())
    readout_parameters = sum(value.numel() for value in readout.parameters())
    receipt = {
        "schema": "butterfly112_coding_finetune_v1",
        "configuration": {
            key: str(value) if isinstance(value, Path) else value
            for key, value in vars(args).items()
        },
        "training_final": last,
        "float_rollout": float_rate,
        "fake_int8_rollout": int8_rate,
        "parameter_accounting": {
            "model_int8_bytes": model_parameters,
            "readout_int8_bytes": readout_parameters,
            "combined_int8_bytes": model_parameters + readout_parameters,
        },
        "contract": {
            "student_state_carried_within_window": True,
            "coding_target_is_one_byte_shifted_teacher_truth": True,
            "zero_initial_state": args.zero_initial_state,
            "integer_inference_implemented": False,
            "native_archive_evidence": False,
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=False)
    torch.save(model.state_dict(), args.output_dir / "model.pt")
    torch.save(readout.state_dict(), args.output_dir / "readout.pt")
    (args.output_dir / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
