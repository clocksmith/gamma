#!/usr/bin/env python3
"""Distill a butterfly branch against the exact teacher probability trace."""

from __future__ import annotations

import argparse
import json
import math
import struct
from pathlib import Path

import numpy as np
import torch
from torch import nn

from train_butterfly112_readout_shadow import (
    prefix_tables,
    quantized_readout_state,
    readout_logits,
)
from train_butterfly112_state_shadow import ButterflyLstm, Trace, fake_int8


def teacher_arrays(path, branch):
    with path.open("rb") as handle:
        header = handle.read(32)
    magic, version, header_bytes, row_bytes, _, rows = struct.unpack(
        "<8sIIIIQ", header
    )
    if (
        magic != b"DPLRTRC1"
        or version != 1
        or header_bytes != 32
        or row_bytes != 9
        or rows % 8
    ):
        raise ValueError("unsupported teacher trace")
    records = np.memmap(
        path,
        mode="r",
        dtype=np.dtype([("probability", "<u2", (4,)), ("truth", "u1")]),
        offset=header_bytes,
        shape=(rows,),
    )
    field = 2 if branch == "main" else 1
    probability = (
        np.asarray(records["probability"][:, field], dtype=np.float32)
        .reshape(-1, 8)
        / 65536.0
    )
    truth_bits = np.asarray(records["truth"]).reshape(-1, 8)
    truth_bytes = np.packbits(truth_bits, axis=1, bitorder="big").reshape(-1)
    return probability, truth_bits.astype(np.float32), truth_bytes


@torch.no_grad()
def evaluate(
    model,
    readout,
    trace,
    teacher_probability,
    truth_bits,
    truth_bytes,
    start,
    rows,
    nodes,
    device,
    reset_interval,
):
    first = trace.batch(np.asarray([start]), device)
    hidden = first[2]
    cell = first[3]
    if reset_interval:
        hidden = torch.zeros_like(hidden)
        cell = torch.zeros_like(cell)
    student_actual = 0.0
    teacher_actual = 0.0
    teacher_kl = 0.0
    epsilon = 1.0 / 65536.0
    for index in range(start, start + rows):
        if reset_interval and (index - start) % reset_interval == 0:
            hidden.zero_()
            cell.zero_()
        batch = trace.batch(np.asarray([index]), device)
        hidden, cell = model(batch[0], batch[1], hidden, cell)
        target_index = index + 1
        byte = torch.tensor(
            [int(truth_bytes[target_index])], dtype=torch.long, device=device
        )
        logits = readout_logits(readout, hidden, byte, nodes)
        student = torch.sigmoid(logits).cpu().numpy()[0]
        teacher = np.clip(
            teacher_probability[target_index], epsilon, 1.0 - epsilon
        )
        truth = truth_bits[target_index]
        student = np.clip(student, epsilon, 1.0 - epsilon)
        student_actual += float(
            -(truth * np.log2(student) + (1.0 - truth) * np.log2(1.0 - student)).sum()
        )
        teacher_actual += float(
            -(truth * np.log2(teacher) + (1.0 - truth) * np.log2(1.0 - teacher)).sum()
        )
        teacher_kl += float(
            (
                teacher * np.log2(teacher / student)
                + (1.0 - teacher) * np.log2((1.0 - teacher) / (1.0 - student))
            ).sum()
        )
    return {
        "bytes": rows,
        "student_actual_bits": student_actual,
        "student_bits_per_byte": student_actual / rows,
        "teacher_actual_bits": teacher_actual,
        "teacher_bits_per_byte": teacher_actual / rows,
        "teacher_kl_bits": teacher_kl,
        "teacher_kl_bits_per_byte": teacher_kl / rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--teacher-trace", type=Path, required=True)
    parser.add_argument("--branch", choices=("main", "side"), required=True)
    parser.add_argument("--input-model", type=Path, required=True)
    parser.add_argument("--input-readout", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--input-rank", type=int, required=True)
    parser.add_argument("--event-rank", type=int, required=True)
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--window", type=int, default=128)
    parser.add_argument("--train-end", type=int, default=540000)
    parser.add_argument("--evaluation-start", type=int, default=560000)
    parser.add_argument("--evaluation-rows", type=int, default=4096)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--state-weight", type=float, default=0.5)
    parser.add_argument("--cell-weight", type=float, default=0.25)
    parser.add_argument("--zero-initial-state", action="store_true")
    parser.add_argument("--threads", type=int, default=6)
    parser.add_argument("--seed", type=int, default=112)
    args = parser.parse_args()

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(args.threads)
    device = torch.device("cpu")
    trace = Trace(args.trace)
    teacher_probability, truth_bits, truth_bytes = teacher_arrays(
        args.teacher_trace, args.branch
    )
    if (
        args.train_end <= args.window
        or args.train_end > trace.rows
        or args.evaluation_start + args.evaluation_rows >= trace.rows
    ):
        raise ValueError("invalid train/evaluation split")
    nodes, _ = prefix_tables(device)

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
            0,
            args.train_end - args.window,
            size=args.batch_size,
            dtype=np.int64,
        )
        indices = starts[:, None] + np.arange(args.window)[None, :]
        flat_indices = indices.reshape(-1)
        flat = trace.batch(flat_indices, device)
        shaped = [
            value.reshape(args.batch_size, args.window, -1) for value in flat
        ]
        x, event, hidden0, cell0, target_hidden, target_cell = shaped
        event = event.reshape(args.batch_size, args.window)
        target_indices = flat_indices + 1
        target_bytes = torch.from_numpy(
            truth_bytes[target_indices]
            .astype(np.int64)
            .reshape(args.batch_size, args.window)
        ).to(device)
        target_probability = torch.from_numpy(
            teacher_probability[target_indices].reshape(
                args.batch_size, args.window, 8
            )
        ).to(device)
        hidden = hidden0[:, 0]
        cell = cell0[:, 0]
        if args.zero_initial_state:
            hidden = torch.zeros_like(hidden)
            cell = torch.zeros_like(cell)
        distillation_loss = torch.zeros((), device=device)
        hidden_loss = torch.zeros((), device=device)
        cell_loss = torch.zeros((), device=device)
        for offset in range(args.window):
            hidden, cell = model(
                x[:, offset], event[:, offset], hidden, cell
            )
            logits = readout_logits(
                readout, hidden, target_bytes[:, offset], nodes
            )
            distillation_loss = (
                distillation_loss
                + nn.functional.binary_cross_entropy_with_logits(
                    logits, target_probability[:, offset]
                )
            )
            hidden_loss = hidden_loss + torch.mean(
                torch.square(hidden - target_hidden[:, offset])
            )
            cell_loss = cell_loss + torch.mean(
                torch.square(cell - target_cell[:, offset])
            )
        distillation_loss = distillation_loss / args.window
        state_loss = (
            hidden_loss + args.cell_weight * cell_loss
        ) / args.window
        loss = distillation_loss + args.state_weight * state_loss
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            list(model.parameters()) + list(readout.parameters()), 5.0
        )
        optimizer.step()
        last = {
            "loss": float(loss.detach()),
            "distillation_loss": float(distillation_loss.detach()),
            "state_loss": float(state_loss.detach()),
        }
        if (step + 1) % 100 == 0:
            print(json.dumps({"step": step + 1} | last), flush=True)

    model.eval()
    readout.eval()
    reset = args.window if args.zero_initial_state else 0
    float_metrics = evaluate(
        model,
        readout,
        trace,
        teacher_probability,
        truth_bits,
        truth_bytes,
        args.evaluation_start,
        args.evaluation_rows,
        nodes,
        device,
        reset,
    )
    float_model = {
        name: value.clone() for name, value in model.state_dict().items()
    }
    float_readout = {
        name: value.clone() for name, value in readout.state_dict().items()
    }
    model.load_state_dict(fake_int8(model))
    readout.load_state_dict(quantized_readout_state(readout))
    int8_metrics = evaluate(
        model,
        readout,
        trace,
        teacher_probability,
        truth_bits,
        truth_bytes,
        args.evaluation_start,
        args.evaluation_rows,
        nodes,
        device,
        reset,
    )
    model.load_state_dict(float_model)
    readout.load_state_dict(float_readout)
    parameters = sum(value.numel() for value in model.parameters()) + sum(
        value.numel() for value in readout.parameters()
    )
    receipt = {
        "schema": "butterfly112_teacher_probability_v1",
        "configuration": {
            key: str(value) if isinstance(value, Path) else value
            for key, value in vars(args).items()
        },
        "training_final": last,
        "float": float_metrics,
        "fake_int8": int8_metrics,
        "parameter_accounting": {"combined_int8_bytes": parameters},
        "contract": {
            "soft_target_is_exact_teacher_branch_probability": True,
            "state_anchor_is_auxiliary": True,
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
