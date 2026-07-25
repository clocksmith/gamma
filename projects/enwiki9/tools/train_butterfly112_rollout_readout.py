#!/usr/bin/env python3
"""Train a prefix readout on the state distribution used by deployment."""

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


@torch.no_grad()
def rollout_states(model, trace, rows, device):
    raw = trace.data[:rows]
    x = torch.from_numpy(np.asarray(raw[:, 1 : trace.inputs + 1])).to(device)
    event_bits = np.asarray(raw[:, 0]).copy().view("<u4")
    event = torch.from_numpy(event_bits.astype(np.int64)).to(device)
    first = trace.batch(np.asarray([0]), device)
    hidden = first[2]
    cell = first[3]
    result = np.empty((rows, trace.cells), dtype=np.float32)
    for index in range(rows):
        hidden, cell = model(
            x[index : index + 1], event[index : index + 1], hidden, cell
        )
        result[index] = hidden[0].cpu().numpy()
        if (index + 1) % 10000 == 0:
            print(json.dumps({"rollout_rows": index + 1}), flush=True)
    return result


@torch.no_grad()
def evaluate(readout, states, targets, indices, node_table, bit_table, device):
    total = 0.0
    for start in range(0, len(indices), 512):
        selected = indices[start : start + 512]
        hidden = torch.from_numpy(states[selected]).to(device)
        target = torch.from_numpy(targets[selected]).to(device)
        logits = readout_logits(readout, hidden, target, node_table)
        bits = bit_table.index_select(0, target)
        loss = nn.functional.binary_cross_entropy_with_logits(
            logits, bits, reduction="sum"
        )
        total += float(loss) / math.log(2.0)
    return {"bytes": len(indices), "bits": total, "bits_per_byte": total / len(indices)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-trace", type=Path, required=True)
    parser.add_argument("--teacher-trace", type=Path, required=True)
    parser.add_argument("--butterfly-model", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--input-rank", type=int, required=True)
    parser.add_argument("--event-rank", type=int, required=True)
    parser.add_argument("--steps", type=int, default=3000)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--learning-rate", type=float, default=3e-3)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--seed", type=int, default=112)
    args = parser.parse_args()

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(args.threads)
    device = torch.device("cpu")
    trace = Trace(args.state_trace)
    teacher_bytes = load_teacher_bytes(args.teacher_trace)
    rows = 120000
    if trace.rows < rows or len(teacher_bytes) <= rows:
        raise ValueError("rollout readout requires 120000 aligned state rows")

    model = ButterflyLstm(
        trace.inputs, trace.cells, args.input_rank, args.event_rank
    ).to(device)
    model.load_state_dict(
        torch.load(args.butterfly_model, map_location=device, weights_only=True)
    )
    model.load_state_dict(fake_int8(model))
    model.eval()
    states = rollout_states(model, trace, rows, device)
    targets = np.asarray(teacher_bytes[1 : rows + 1], dtype=np.int64)
    node_table, bit_table = prefix_tables(device)

    readout = nn.Linear(trace.cells, 255, bias=True).to(device)
    optimizer = torch.optim.AdamW(readout.parameters(), lr=args.learning_rate)
    rng = np.random.default_rng(args.seed)
    train_end = 84000
    development_end = 102000
    for step in range(args.steps):
        indices = rng.integers(0, train_end, size=args.batch_size)
        hidden = torch.from_numpy(states[indices]).to(device)
        target = torch.from_numpy(targets[indices]).to(device)
        logits = readout_logits(readout, hidden, target, node_table)
        bits = bit_table.index_select(0, target)
        loss = nn.functional.binary_cross_entropy_with_logits(logits, bits)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        if (step + 1) % 250 == 0:
            print(
                json.dumps({"step": step + 1, "loss": float(loss.detach())}),
                flush=True,
            )

    holdout = np.arange(development_end, rows, dtype=np.int64)
    readout.eval()
    float_metrics = evaluate(
        readout, states, targets, holdout, node_table, bit_table, device
    )
    readout.load_state_dict(quantized_readout_state(readout))
    quantized_metrics = evaluate(
        readout, states, targets, holdout, node_table, bit_table, device
    )
    model_parameters = sum(value.numel() for value in model.parameters())
    readout_parameters = sum(value.numel() for value in readout.parameters())
    receipt = {
        "schema": "butterfly112_rollout_readout_v1",
        "configuration": {
            key: str(value) if isinstance(value, Path) else value
            for key, value in vars(args).items()
        },
        "float": float_metrics,
        "quantized": quantized_metrics,
        "parameter_accounting": {
            "model_int8_bytes": model_parameters,
            "readout_int8_bytes": readout_parameters,
            "combined_int8_bytes": model_parameters + readout_parameters,
        },
        "contract": {
            "readout_trained_on_quantized_student_rollout": True,
            "causal_one_byte_shift": True,
            "integer_inference_implemented": False,
            "native_archive_evidence": False,
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=False)
    np.save(args.output_dir / "rollout_states.npy", states)
    torch.save(readout.state_dict(), args.output_dir / "readout_fake_int8.pt")
    (args.output_dir / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
