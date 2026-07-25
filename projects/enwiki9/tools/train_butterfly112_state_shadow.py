#!/usr/bin/env python3
"""Train a full-rank structured LSTM transition against a DPLRST2 trace."""

from __future__ import annotations

import argparse
import json
import math
import random
import struct
from pathlib import Path

import numpy as np
import torch
from torch import nn


HEADER_BYTES = 28
MAGIC = b"DPLRST2\0"


class Trace:
    def __init__(self, path: Path) -> None:
        with path.open("rb") as handle:
            header = handle.read(HEADER_BYTES)
        magic, version, inputs, cells, row_bytes, model_index = struct.unpack(
            "<8s5I", header
        )
        if magic != MAGIC or version != 2:
            raise ValueError(f"unsupported trace header: {magic!r} v{version}")
        if row_bytes != (inputs + 1 + 4 * cells) * 4:
            raise ValueError("trace row size does not match DPLRST2 fields")
        payload = path.stat().st_size - HEADER_BYTES
        if payload <= 0 or payload % row_bytes:
            raise ValueError("truncated or empty trace")
        self.path = path
        self.inputs = inputs
        self.cells = cells
        self.row_floats = row_bytes // 4
        self.rows = payload // row_bytes
        self.model_index = model_index
        self.data = np.memmap(
            path,
            mode="r",
            dtype="<f4",
            offset=HEADER_BYTES,
            shape=(self.rows, self.row_floats),
        )

    def batch(self, indices: np.ndarray, device: torch.device):
        rows = np.asarray(self.data[indices], dtype=np.float32)
        p = self.inputs
        n = self.cells
        event_bits = rows[:, 0].copy().view("<u4")
        event = torch.from_numpy(event_bits.astype(np.int64)).to(device)
        x = torch.from_numpy(rows[:, 1 : p + 1]).to(device)
        h0 = torch.from_numpy(rows[:, p + 1 : p + 1 + n]).to(device)
        c0 = torch.from_numpy(rows[:, p + 1 + n : p + 1 + 2 * n]).to(device)
        h1 = torch.from_numpy(rows[:, p + 1 + 2 * n : p + 1 + 3 * n]).to(
            device
        )
        c1 = torch.from_numpy(rows[:, p + 1 + 3 * n : p + 1 + 4 * n]).to(
            device
        )
        return x, event, h0, c0, h1, c1


class ButterflyLstm(nn.Module):
    def __init__(
        self, inputs: int, cells: int, input_rank: int, event_rank: int
    ) -> None:
        super().__init__()
        self.inputs = inputs
        self.cells = cells
        self.input_rank = input_rank
        self.event_rank = event_rank
        self.width = 1 << math.ceil(math.log2(cells))
        self.stages = int(math.log2(self.width))
        self.input_projection = nn.Linear(inputs, input_rank, bias=False)
        self.gate_expansion = nn.Linear(input_rank, 4 * cells, bias=False)
        self.diagonal = nn.Parameter(torch.ones(4, cells))
        self.event_embedding = nn.Embedding(inputs, event_rank)
        self.event_expansion = nn.Linear(event_rank, 4 * cells, bias=False)
        self.bias = nn.Parameter(torch.zeros(4, cells))
        weights = torch.empty(self.stages, 4, self.width // 2, 2, 2)
        nn.init.normal_(weights, mean=0.0, std=0.035)
        weights[..., 0, 0] += 1.0
        weights[..., 1, 1] += 1.0
        self.butterfly = nn.Parameter(weights)

        pairs = []
        for stage in range(self.stages):
            stride = 1 << stage
            group = stride << 1
            left = []
            right = []
            for base in range(0, self.width, group):
                for offset in range(stride):
                    left.append(base + offset)
                    right.append(base + offset + stride)
            pairs.append(
                (
                    torch.tensor(left, dtype=torch.long),
                    torch.tensor(right, dtype=torch.long),
                )
            )
        for stage, (left, right) in enumerate(pairs):
            self.register_buffer(f"left_{stage}", left)
            self.register_buffer(f"right_{stage}", right)

    def recurrent(self, hidden: torch.Tensor) -> torch.Tensor:
        batch = hidden.shape[0]
        padded = hidden.new_zeros(batch, 4, self.width)
        padded[:, :, : self.cells] = hidden[:, None, :]
        for stage in range(self.stages):
            left = getattr(self, f"left_{stage}")
            right = getattr(self, f"right_{stage}")
            pair = torch.stack(
                (padded.index_select(2, left), padded.index_select(2, right)),
                dim=-1,
            )
            mixed = torch.einsum(
                "bgpi,gpij->bgpj", pair, self.butterfly[stage]
            )
            next_value = torch.empty_like(padded)
            next_value[:, :, left] = mixed[..., 0]
            next_value[:, :, right] = mixed[..., 1]
            padded = next_value
        return padded[:, :, : self.cells]

    def forward(self, x, event, hidden, cell):
        input_term = self.gate_expansion(self.input_projection(x))
        preactivation = input_term.view(-1, 4, self.cells)
        preactivation = (
            preactivation
            + self.recurrent(hidden)
            + self.diagonal[None, :, :] * hidden[:, None, :]
            + self.event_expansion(self.event_embedding(event)).view(
                -1, 4, self.cells
            )
            + self.bias[None, :, :]
        )
        i, f, o, g = preactivation.unbind(dim=1)
        next_cell = torch.sigmoid(f) * cell + torch.sigmoid(i) * torch.tanh(g)
        next_hidden = torch.sigmoid(o) * torch.tanh(next_cell)
        return next_hidden, next_cell

    def operation_count(self) -> int:
        projection = self.inputs * self.input_rank
        expansion = 4 * self.cells * self.input_rank
        event = self.inputs * self.event_rank + 4 * self.cells * self.event_rank
        butterfly = self.stages * 4 * (self.width // 2) * 4
        diagonal = 4 * self.cells
        return projection + expansion + event + butterfly + diagonal


def fake_int8(model: nn.Module) -> dict[str, torch.Tensor]:
    state = {}
    for name, value in model.state_dict().items():
        if not value.is_floating_point() or name.startswith(("left_", "right_")):
            state[name] = value.clone()
            continue
        limit = float(value.abs().max())
        scale = limit / 127.0 if limit else 1.0
        state[name] = (value / scale).round().clamp(-127, 127) * scale
    return state


@torch.no_grad()
def evaluate(model, trace, indices, batch_size, device):
    hidden_squared = 0.0
    cell_squared = 0.0
    values = 0
    for start in range(0, len(indices), batch_size):
        batch = trace.batch(indices[start : start + batch_size], device)
        predicted_hidden, predicted_cell = model(*batch[:4])
        hidden_squared += torch.square(predicted_hidden - batch[4]).sum().item()
        cell_squared += torch.square(predicted_cell - batch[5]).sum().item()
        values += predicted_hidden.numel()
    return {
        "hidden_mse": hidden_squared / values,
        "cell_mse": cell_squared / values,
    }


@torch.no_grad()
def evaluate_rollout(model, trace, start, rows, device):
    first = trace.batch(np.asarray([start]), device)
    hidden = first[2]
    cell = first[3]
    hidden_squared = 0.0
    cell_squared = 0.0
    values = 0
    for index in range(start, start + rows):
        batch = trace.batch(np.asarray([index]), device)
        hidden, cell = model(batch[0], batch[1], hidden, cell)
        hidden_squared += torch.square(hidden - batch[4]).sum().item()
        cell_squared += torch.square(cell - batch[5]).sum().item()
        values += hidden.numel()
    return {
        "rows": rows,
        "hidden_mse": hidden_squared / values,
        "cell_mse": cell_squared / values,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--input-rank", type=int, choices=(1, 2, 4, 8, 16))
    parser.add_argument("--event-rank", type=int, default=16)
    parser.add_argument("--steps", type=int, default=4000)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--learning-rate", type=float, default=3e-3)
    parser.add_argument("--cell-weight", type=float, default=0.25)
    parser.add_argument("--development-rows", type=int, default=16384)
    parser.add_argument("--rollout-rows", type=int, default=4096)
    parser.add_argument("--load-model", type=Path)
    parser.add_argument("--threads", type=int, default=6)
    parser.add_argument("--seed", type=int, default=112)
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(args.threads)
    device = torch.device("cpu")
    trace = Trace(args.trace)
    split = int(trace.rows * 0.9)
    if split <= args.batch_size or trace.rows - split < args.development_rows:
        raise ValueError("trace is too small for the requested split")

    model = ButterflyLstm(
        trace.inputs, trace.cells, args.input_rank, args.event_rank
    ).to(device)
    if args.load_model:
        model.load_state_dict(
            torch.load(args.load_model, map_location=device, weights_only=True)
        )
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    rng = np.random.default_rng(args.seed)

    model.train()
    last_loss = None
    for step in range(0 if args.load_model else args.steps):
        indices = rng.integers(0, split, size=args.batch_size)
        batch = trace.batch(indices, device)
        predicted_hidden, predicted_cell = model(*batch[:4])
        hidden_loss = torch.mean(torch.square(predicted_hidden - batch[4]))
        cell_loss = torch.mean(torch.square(predicted_cell - batch[5]))
        loss = hidden_loss + args.cell_weight * cell_loss
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        last_loss = float(loss.detach())
        if (step + 1) % 250 == 0:
            print(json.dumps({"step": step + 1, "loss": last_loss}), flush=True)

    dev_indices = np.linspace(
        split, trace.rows - 1, args.development_rows, dtype=np.int64
    )
    model.eval()
    float_metrics = evaluate(
        model, trace, dev_indices, args.batch_size, device
    )
    float_rollout = evaluate_rollout(
        model, trace, split, args.rollout_rows, device
    )
    float_state = {name: value.clone() for name, value in model.state_dict().items()}
    model.load_state_dict(fake_int8(model))
    int8_metrics = evaluate(
        model, trace, dev_indices, args.batch_size, device
    )
    int8_rollout = evaluate_rollout(
        model, trace, split, args.rollout_rows, device
    )
    model.load_state_dict(float_state)

    parameter_count = sum(parameter.numel() for parameter in model.parameters())
    metrics = {
        "trace": str(args.trace),
        "trace_rows": trace.rows,
        "model_index": trace.model_index,
        "cells": trace.cells,
        "input_rank": args.input_rank,
        "event_rank": args.event_rank,
        "steps": args.steps,
        "batch_size": args.batch_size,
        "training_final_loss": last_loss,
        "development": float_metrics,
        "development_rollout": float_rollout,
        "development_fake_int8": int8_metrics,
        "development_rollout_fake_int8": int8_rollout,
        "parameter_count": parameter_count,
        "float_parameter_bytes": parameter_count * 4,
        "int8_parameter_bytes": parameter_count,
        "estimated_multiply_accumulates_per_step": model.operation_count(),
    }
    args.output_dir.mkdir(parents=True, exist_ok=False)
    torch.save(model.state_dict(), args.output_dir / "model.pt")
    (args.output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
