#!/usr/bin/env python3
"""Train a row-scaled 1-bit version of the exact three-transform LSTM."""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

import numpy as np
import torch
from torch import nn

from train_butterfly112_state_shadow import Trace


def load_one_layer_snapshot(path):
    with path.open("rb") as handle:
        header = handle.read(28)
        magic, version, inputs, outputs, cells, layers = struct.unpack(
            "<8s5I", header
        )
        values = np.fromfile(handle, dtype="<f4")
    if (
        magic != b"DPLRWGT1"
        or version != 1
        or cells != 112
        or layers != 1
    ):
        raise ValueError("binary state screen currently requires one layer")
    output_count = outputs * (cells + 1)
    output = values[:output_count].reshape(outputs, cells + 1)
    columns = outputs + 1 + cells + inputs
    recurrent = values[output_count:].reshape(3, cells, columns)
    return {
        "inputs": inputs,
        "outputs": outputs,
        "cells": cells,
        "output": output,
        "recurrent": recurrent,
    }


def binary_ste(weights):
    scale = torch.mean(torch.abs(weights), dim=-1, keepdim=True)
    quantized = torch.where(weights >= 0.0, scale, -scale)
    return weights + (quantized - weights).detach()


def ternary_ste(weights):
    absolute = torch.abs(weights)
    threshold = 0.7 * torch.mean(absolute, dim=-1, keepdim=True)
    mask = absolute >= threshold
    count = mask.sum(dim=-1, keepdim=True).clamp_min(1)
    scale = torch.sum(absolute * mask, dim=-1, keepdim=True) / count
    quantized = torch.sign(weights) * scale * mask
    return weights + (quantized - weights).detach()


class BinaryLstm112(nn.Module):
    def __init__(
        self, snapshot, input_node_bits=1, other_gate_bits=1
    ):
        super().__init__()
        self.inputs = snapshot["inputs"]
        self.outputs = snapshot["outputs"]
        self.cells = snapshot["cells"]
        self.input_node_bits = input_node_bits
        self.other_gate_bits = other_gate_bits
        self.weights = nn.Parameter(torch.from_numpy(snapshot["recurrent"].copy()))
        self.gamma = nn.Parameter(torch.ones(3, self.cells))
        self.beta = nn.Parameter(torch.zeros(3, self.cells))

    def forward(self, x, event, hidden, cell):
        weights = torch.stack(
            (
                ternary_ste(self.weights[0])
                if self.other_gate_bits == 2
                else binary_ste(self.weights[0]),
                ternary_ste(self.weights[1])
                if self.input_node_bits == 2
                else binary_ste(self.weights[1]),
                ternary_ste(self.weights[2])
                if self.other_gate_bits == 2
                else binary_ste(self.weights[2]),
            )
        )
        event_weights = weights[:, :, : self.outputs].permute(2, 0, 1)
        event_term = event_weights.index_select(0, event)
        continuous = torch.cat(
            (x, hidden, torch.ones_like(hidden[:, :1])), dim=1
        )
        continuous_weights = weights[:, :, self.outputs :]
        preactivation = event_term + torch.einsum(
            "bi,gni->bgn", continuous, continuous_weights
        )
        normalized = preactivation / torch.sqrt(
            torch.mean(torch.square(preactivation), dim=2, keepdim=True)
            + 1.0e-5
        )
        activated = normalized * self.gamma[None, :, :] + self.beta[None, :, :]
        forget = torch.sigmoid(activated[:, 0])
        node = torch.tanh(activated[:, 1])
        output = torch.sigmoid(activated[:, 2])
        next_cell = cell * forget + node * (1.0 - forget)
        next_hidden = output * torch.tanh(next_cell)
        return next_hidden, next_cell

    def parameter_bytes(self):
        rows = 3 * self.cells
        gate_values = self.weights[0].numel()
        packed = (
            gate_values
            * (2 * self.other_gate_bits + self.input_node_bits)
            + 7
        ) // 8
        scales = rows * 2
        normalization = (self.gamma.numel() + self.beta.numel()) * 2
        return {
            "packed_binary_weight_bytes": packed,
            "input_node_weight_bits": self.input_node_bits,
            "other_gate_weight_bits": self.other_gate_bits,
            "fp16_row_scale_bytes": scales,
            "fp16_gamma_beta_bytes": normalization,
            "total_bytes": packed + scales + normalization,
        }


@torch.no_grad()
def evaluate(model, trace, indices, batch_size, device):
    hidden_error = 0.0
    cell_error = 0.0
    values = 0
    for start in range(0, len(indices), batch_size):
        batch = trace.batch(indices[start : start + batch_size], device)
        hidden, cell = model(*batch[:4])
        hidden_error += torch.square(hidden - batch[4]).sum().item()
        cell_error += torch.square(cell - batch[5]).sum().item()
        values += hidden.numel()
    return {
        "rows": len(indices),
        "hidden_mse": hidden_error / values,
        "cell_mse": cell_error / values,
    }


@torch.no_grad()
def rollout(model, trace, start, rows, device):
    first = trace.batch(np.asarray([start]), device)
    hidden = first[2]
    cell = first[3]
    hidden_error = 0.0
    cell_error = 0.0
    values = 0
    for index in range(start, start + rows):
        batch = trace.batch(np.asarray([index]), device)
        hidden, cell = model(batch[0], batch[1], hidden, cell)
        hidden_error += torch.square(hidden - batch[4]).sum().item()
        cell_error += torch.square(cell - batch[5]).sum().item()
        values += hidden.numel()
    return {
        "rows": rows,
        "hidden_mse": hidden_error / values,
        "cell_mse": cell_error / values,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=4000)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--cell-weight", type=float, default=0.25)
    parser.add_argument("--rollout-rows", type=int, default=4096)
    parser.add_argument(
        "--input-node-bits", type=int, choices=(1, 2), default=1
    )
    parser.add_argument(
        "--other-gate-bits", type=int, choices=(1, 2), default=1
    )
    parser.add_argument("--threads", type=int, default=6)
    parser.add_argument("--seed", type=int, default=112)
    args = parser.parse_args()

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(args.threads)
    device = torch.device("cpu")
    trace = Trace(args.trace)
    snapshot = load_one_layer_snapshot(args.snapshot)
    if snapshot["inputs"] != trace.inputs or snapshot["cells"] != trace.cells:
        raise ValueError("trace/snapshot shape mismatch")
    model = BinaryLstm112(
        snapshot, args.input_node_bits, args.other_gate_bits
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    train_end = 84000
    development_end = 102000
    rng = np.random.default_rng(args.seed)

    model.train()
    last = None
    for step in range(args.steps):
        indices = rng.integers(0, train_end, size=args.batch_size)
        batch = trace.batch(indices, device)
        hidden, cell = model(*batch[:4])
        hidden_loss = torch.mean(torch.square(hidden - batch[4]))
        cell_loss = torch.mean(torch.square(cell - batch[5]))
        loss = hidden_loss + args.cell_weight * cell_loss
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        last = {
            "loss": float(loss.detach()),
            "hidden_mse": float(hidden_loss.detach()),
            "cell_mse": float(cell_loss.detach()),
        }
        if (step + 1) % 250 == 0:
            print(json.dumps({"step": step + 1} | last), flush=True)

    model.eval()
    holdout = np.arange(development_end, 120000, dtype=np.int64)
    receipt = {
        "schema": "binary112_state_shadow_v1",
        "configuration": {
            key: str(value) if isinstance(value, Path) else value
            for key, value in vars(args).items()
        },
        "training_final": last,
        "holdout": evaluate(
            model, trace, holdout, args.batch_size, device
        ),
        "holdout_rollout": rollout(
            model, trace, development_end, args.rollout_rows, device
        ),
        "parameter_accounting": model.parameter_bytes(),
        "contract": {
            "full_dense_interaction_rank": True,
            "row_scaled_binary_weights_with_ste": True,
            "exact_three_transform_cell_equations": True,
            "integer_inference_implemented": False,
            "native_archive_evidence": False,
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=False)
    torch.save(model.state_dict(), args.output_dir / "model.pt")
    np.save(args.output_dir / "teacher_output.npy", snapshot["output"])
    (args.output_dir / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
