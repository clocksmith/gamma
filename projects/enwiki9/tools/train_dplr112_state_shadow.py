#!/usr/bin/env python3
"""Fit and screen a DPLR transition against sealed endpoint428 state traces."""

import argparse
import hashlib
import json
import struct
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn


HEADER = struct.Struct("<8s5I")


class StateTrace:
    def __init__(self, path):
        self.path = Path(path).resolve()
        with self.path.open("rb") as handle:
            magic, version, inputs, cells, row_bytes, _ = HEADER.unpack(
                handle.read(HEADER.size)
            )
        if magic != b"DPLRST2\0" or version != 2:
            raise ValueError("unsupported state trace")
        if row_bytes != 4 * (1 + inputs + 4 * cells):
            raise ValueError("invalid row size")
        payload = self.path.stat().st_size - HEADER.size
        if payload < 0 or payload % row_bytes:
            raise ValueError("truncated state trace")
        self.inputs = inputs
        self.cells = cells
        self.rows = payload // row_bytes
        self.words = np.memmap(
            self.path,
            mode="r",
            dtype="<u4",
            offset=HEADER.size,
            shape=(self.rows, row_bytes // 4),
        )

    def take(self, indices):
        words = np.asarray(self.words[indices])
        symbol = words[:, 0].astype(np.int64)
        values = words[:, 1:].view("<f4")
        i = self.inputs
        c = self.cells
        return (
            values[:, :i],
            symbol,
            values[:, i : i + c],
            values[:, i + c : i + 2 * c],
            values[:, i + 2 * c : i + 3 * c],
            values[:, i + 3 * c : i + 4 * c],
        )


class DplrTransition(nn.Module):
    def __init__(self, inputs, cells, rank, event_rank):
        super().__init__()
        self.projection = nn.Parameter(torch.empty(rank, inputs + cells))
        self.expansion = nn.Parameter(torch.empty(3, cells, rank))
        self.diagonal = nn.Parameter(torch.empty(3, cells))
        self.event = nn.Embedding(256, event_rank)
        self.event_expansion = nn.Parameter(torch.empty(3, cells, event_rank))
        self.bias = nn.Parameter(torch.zeros(3, cells))
        nn.init.normal_(self.projection, std=0.02)
        nn.init.normal_(self.expansion, std=0.02)
        nn.init.normal_(self.diagonal, mean=0.0, std=0.02)
        nn.init.normal_(self.event.weight, std=0.02)
        nn.init.normal_(self.event_expansion, std=0.02)
        with torch.no_grad():
            self.bias[0].fill_(1.0)

    def forward(self, features, symbol, hidden, cell):
        combined = torch.cat((features, hidden), dim=1)
        projected = combined @ self.projection.t()
        event = self.event(symbol)
        gates = torch.einsum("br,gcr->bgc", projected, self.expansion)
        gates = gates + self.diagonal.unsqueeze(0) * hidden.unsqueeze(1)
        gates = gates + torch.einsum(
            "be,gce->bgc", event, self.event_expansion
        )
        gates = gates + self.bias.unsqueeze(0)
        forget = torch.sigmoid(gates[:, 0])
        node = torch.tanh(gates[:, 1])
        output = torch.sigmoid(gates[:, 2])
        next_cell = forget * cell + (1.0 - forget) * node
        next_hidden = output * torch.tanh(next_cell)
        return next_hidden, next_cell


def tensors(batch, device):
    return tuple(torch.from_numpy(np.array(x, copy=True)).to(device) for x in batch)


def evaluate(model, trace, start, stop, batch_size, device):
    totals = dict(h_sq=0.0, c_sq=0.0, persist_h_sq=0.0, persist_c_sq=0.0)
    count = 0
    model.eval()
    with torch.no_grad():
        for left in range(start, stop, batch_size):
            right = min(left + batch_size, stop)
            x, symbol, h, c, target_h, target_c = tensors(
                trace.take(np.arange(left, right)), device
            )
            pred_h, pred_c = model(x, symbol.long(), h, c)
            totals["h_sq"] += torch.sum((pred_h - target_h) ** 2).item()
            totals["c_sq"] += torch.sum((pred_c - target_c) ** 2).item()
            totals["persist_h_sq"] += torch.sum((h - target_h) ** 2).item()
            totals["persist_c_sq"] += torch.sum((c - target_c) ** 2).item()
            count += (right - left) * trace.cells
    return {
        "rows": stop - start,
        "hidden_rmse": (totals["h_sq"] / count) ** 0.5,
        "cell_rmse": (totals["c_sq"] / count) ** 0.5,
        "persistence_hidden_rmse": (totals["persist_h_sq"] / count) ** 0.5,
        "persistence_cell_rmse": (totals["persist_c_sq"] / count) ** 0.5,
    }


def rollout(model, trace, start, rows, device):
    stop = min(start + rows, trace.rows)
    first = tensors(trace.take(np.array([start])), device)
    hidden, cell = first[2], first[3]
    h_sq = c_sq = 0.0
    count = 0
    model.eval()
    with torch.no_grad():
        for index in range(start, stop):
            x, symbol, _, _, target_h, target_c = tensors(
                trace.take(np.array([index])), device
            )
            hidden, cell = model(x, symbol.long(), hidden, cell)
            h_sq += torch.sum((hidden - target_h) ** 2).item()
            c_sq += torch.sum((cell - target_c) ** 2).item()
            count += trace.cells
    return {
        "rows": stop - start,
        "hidden_rmse": (h_sq / count) ** 0.5,
        "cell_rmse": (c_sq / count) ** 0.5,
    }


def quantize(model):
    packed = {}
    restored = {}
    raw_bytes = 0
    for name, value in model.state_dict().items():
        array = value.detach().cpu().numpy()
        scale = max(float(np.max(np.abs(array))) / 127.0, 1e-12)
        quantized = np.clip(np.rint(array / scale), -127, 127).astype(np.int8)
        packed[name] = quantized
        packed[name + ".scale"] = np.array(scale, dtype=np.float32)
        restored[name] = torch.from_numpy(quantized.astype(np.float32) * scale)
        raw_bytes += quantized.nbytes + 4
    return packed, restored, raw_bytes


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", required=True)
    parser.add_argument(
        "--rank", type=int, choices=(1, 2, 4, 8, 16, 32), required=True
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--steps", type=int, default=2000)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--event-rank", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=0.003)
    parser.add_argument("--state-weight", type=float, default=1.0)
    parser.add_argument("--rollout-rows", type=int, default=4096)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--seed", type=int, default=428112)
    args = parser.parse_args()

    torch.set_num_threads(args.threads)
    torch.manual_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    device = torch.device("cpu")
    trace = StateTrace(args.trace)
    train_stop = int(trace.rows * 0.70)
    dev_stop = int(trace.rows * 0.85)
    model = DplrTransition(
        trace.inputs, trace.cells, args.rank, args.event_rank
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    started = time.monotonic()
    history = []

    model.train()
    for step in range(1, args.steps + 1):
        indices = rng.integers(0, train_stop, size=args.batch_size)
        x, symbol, h, c, target_h, target_c = tensors(trace.take(indices), device)
        pred_h, pred_c = model(x, symbol.long(), h, c)
        loss_h = torch.mean((pred_h - target_h) ** 2)
        loss_c = torch.mean((pred_c - target_c) ** 2)
        loss = loss_h + args.state_weight * loss_c
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        if step == 1 or step % 100 == 0 or step == args.steps:
            row = {
                "step": step,
                "loss": float(loss.detach()),
                "hidden_mse": float(loss_h.detach()),
                "cell_mse": float(loss_c.detach()),
                "elapsed_seconds": time.monotonic() - started,
            }
            history.append(row)
            print(json.dumps(row), flush=True)

    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    float_dev = evaluate(
        model, trace, train_stop, dev_stop, args.batch_size, device
    )
    float_holdout = evaluate(
        model, trace, dev_stop, trace.rows, args.batch_size, device
    )
    float_rollout = rollout(
        model, trace, dev_stop, args.rollout_rows, device
    )

    packed, restored, raw_bytes = quantize(model)
    parameter_path = output / "parameters_int8.npz"
    np.savez_compressed(parameter_path, **packed)
    quantized_model = DplrTransition(
        trace.inputs, trace.cells, args.rank, args.event_rank
    ).to(device)
    quantized_model.load_state_dict(restored)
    quantized_holdout = evaluate(
        quantized_model, trace, dev_stop, trace.rows, args.batch_size, device
    )
    quantized_rollout = rollout(
        quantized_model, trace, dev_stop, args.rollout_rows, device
    )
    receipt = {
        "schema": "dplr112_state_shadow_v1",
        "configuration": vars(args),
        "trace": {
            "path": str(trace.path),
            "bytes": trace.path.stat().st_size,
            "sha256": sha256(trace.path),
            "rows": trace.rows,
            "inputs": trace.inputs,
            "cells": trace.cells,
        },
        "splits": {
            "train": [0, train_stop],
            "development": [train_stop, dev_stop],
            "holdout": [dev_stop, trace.rows],
        },
        "training": {
            "elapsed_seconds": time.monotonic() - started,
            "history": history,
        },
        "float": {
            "development": float_dev,
            "holdout": float_holdout,
            "holdout_rollout": float_rollout,
        },
        "quantized": {
            "holdout": quantized_holdout,
            "holdout_rollout": quantized_rollout,
        },
        "parameter_accounting": {
            "int8_plus_scale_bytes": raw_bytes,
            "compressed_npz_bytes": parameter_path.stat().st_size,
            "compressed_npz_sha256": sha256(parameter_path),
        },
        "contract": {
            "teacher_previous_state_used_for_one_step_fit": True,
            "autonomous_rollout_uses_student_state": True,
            "quantized_screen_uses_dequantized_int8_parameters": True,
            "integer_inference_implemented": False,
            "native_archive_evidence": False,
        },
    }
    receipt_path = output / "receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"receipt": str(receipt_path), **receipt["quantized"]}))


if __name__ == "__main__":
    main()
