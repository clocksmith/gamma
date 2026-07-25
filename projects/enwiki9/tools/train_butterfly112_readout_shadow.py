#!/usr/bin/env python3
"""Measure butterfly-state coding value with a 255-node prefix readout."""

from __future__ import annotations

import argparse
import json
import math
import struct
from pathlib import Path

import numpy as np
import torch
from torch import nn

from train_butterfly112_state_shadow import ButterflyLstm, Trace, fake_int8


def prefix_tables(device):
    nodes = np.empty((256, 8), dtype=np.int64)
    bits = np.empty((256, 8), dtype=np.float32)
    for value in range(256):
        node = 0
        for position, shift in enumerate(range(7, -1, -1)):
            bit = (value >> shift) & 1
            nodes[value, position] = node
            bits[value, position] = bit
            node = 2 * node + 1 + bit
    return (
        torch.from_numpy(nodes).to(device),
        torch.from_numpy(bits).to(device),
    )


def load_teacher_bytes(path):
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
    return np.packbits(
        np.asarray(records["truth"]).reshape(-1, 8), axis=1, bitorder="big"
    ).reshape(-1)


def target_bytes(teacher_bytes, indices, device):
    values = np.asarray(teacher_bytes[indices], dtype=np.int64)
    return torch.from_numpy(values).to(device)


def readout_logits(readout, hidden, targets, node_table):
    all_logits = readout(hidden)
    nodes = node_table.index_select(0, targets)
    return all_logits.gather(1, nodes)


def bit_cost(readout, hidden, targets, node_table, bit_table):
    logits = readout_logits(readout, hidden, targets, node_table)
    bits = bit_table.index_select(0, targets)
    loss = nn.functional.binary_cross_entropy_with_logits(
        logits, bits, reduction="sum"
    )
    return float(loss) / math.log(2.0)


@torch.no_grad()
def evaluate_teacher(
    readout, trace, teacher_bytes, indices, node_table, bit_table, device
):
    total = 0.0
    batch_size = 512
    for start in range(0, len(indices), batch_size):
        selected = indices[start : start + batch_size]
        batch = trace.batch(selected, device)
        targets = target_bytes(teacher_bytes, selected + 1, device)
        total += bit_cost(readout, batch[4], targets, node_table, bit_table)
    return {"bytes": len(indices), "bits": total, "bits_per_byte": total / len(indices)}


@torch.no_grad()
def evaluate_one_step(
    model, readout, trace, teacher_bytes, indices, node_table, bit_table, device
):
    total = 0.0
    batch_size = 512
    for start in range(0, len(indices), batch_size):
        selected = indices[start : start + batch_size]
        batch = trace.batch(selected, device)
        hidden, _ = model(*batch[:4])
        targets = target_bytes(teacher_bytes, selected + 1, device)
        total += bit_cost(readout, hidden, targets, node_table, bit_table)
    return {"bytes": len(indices), "bits": total, "bits_per_byte": total / len(indices)}


@torch.no_grad()
def evaluate_rollout(
    model,
    readout,
    trace,
    teacher_bytes,
    start,
    rows,
    node_table,
    bit_table,
    device,
):
    first = trace.batch(np.asarray([start]), device)
    hidden = first[2]
    cell = first[3]
    total = 0.0
    for index in range(start, start + rows):
        batch = trace.batch(np.asarray([index]), device)
        hidden, cell = model(batch[0], batch[1], hidden, cell)
        targets = target_bytes(
            teacher_bytes, np.asarray([index + 1]), device
        )
        total += bit_cost(readout, hidden, targets, node_table, bit_table)
    return {"bytes": rows, "bits": total, "bits_per_byte": total / rows}


def quantized_readout_state(readout):
    state = {}
    for name, value in readout.state_dict().items():
        limit = float(value.abs().max())
        scale = limit / 127.0 if limit else 1.0
        state[name] = (value / scale).round().clamp(-127, 127) * scale
    return state


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
    parser.add_argument("--rollout-rows", type=int, default=4096)
    parser.add_argument("--threads", type=int, default=6)
    parser.add_argument("--seed", type=int, default=112)
    args = parser.parse_args()

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(args.threads)
    device = torch.device("cpu")
    trace = Trace(args.state_trace)
    teacher_bytes = load_teacher_bytes(args.teacher_trace)
    if trace.rows < 120000:
        raise ValueError("the comparable split requires 120000 state rows")
    if len(teacher_bytes) <= 120000:
        raise ValueError("teacher trace lacks one-byte-shifted targets")
    train_end = 84000
    development_end = 102000
    holdout_end = 119999
    node_table, bit_table = prefix_tables(device)

    model = ButterflyLstm(
        trace.inputs, trace.cells, args.input_rank, args.event_rank
    ).to(device)
    model.load_state_dict(
        torch.load(args.butterfly_model, map_location=device, weights_only=True)
    )
    model.eval()

    readout = nn.Linear(trace.cells, 255, bias=True).to(device)
    optimizer = torch.optim.AdamW(readout.parameters(), lr=args.learning_rate)
    rng = np.random.default_rng(args.seed)
    for step in range(args.steps):
        indices = rng.integers(0, train_end, size=args.batch_size)
        batch = trace.batch(indices, device)
        targets = target_bytes(teacher_bytes, indices + 1, device)
        logits = readout_logits(readout, batch[4], targets, node_table)
        bits = bit_table.index_select(0, targets)
        loss = nn.functional.binary_cross_entropy_with_logits(logits, bits)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        if (step + 1) % 250 == 0:
            print(
                json.dumps({"step": step + 1, "loss": float(loss.detach())}),
                flush=True,
            )

    holdout = np.arange(development_end, holdout_end, dtype=np.int64)
    readout.eval()
    float_metrics = {
        "teacher_state_holdout": evaluate_teacher(
            readout,
            trace,
            teacher_bytes,
            holdout,
            node_table,
            bit_table,
            device,
        ),
        "butterfly_one_step_holdout": evaluate_one_step(
            model,
            readout,
            trace,
            teacher_bytes,
            holdout,
            node_table,
            bit_table,
            device,
        ),
        "butterfly_rollout_holdout": evaluate_rollout(
            model,
            readout,
            trace,
            teacher_bytes,
            development_end,
            args.rollout_rows,
            node_table,
            bit_table,
            device,
        ),
    }

    float_model_state = {
        name: value.clone() for name, value in model.state_dict().items()
    }
    float_readout_state = {
        name: value.clone() for name, value in readout.state_dict().items()
    }
    model.load_state_dict(fake_int8(model))
    readout.load_state_dict(quantized_readout_state(readout))
    quantized_metrics = {
        "teacher_state_holdout": evaluate_teacher(
            readout,
            trace,
            teacher_bytes,
            holdout,
            node_table,
            bit_table,
            device,
        ),
        "butterfly_one_step_holdout": evaluate_one_step(
            model,
            readout,
            trace,
            teacher_bytes,
            holdout,
            node_table,
            bit_table,
            device,
        ),
        "butterfly_rollout_holdout": evaluate_rollout(
            model,
            readout,
            trace,
            teacher_bytes,
            development_end,
            args.rollout_rows,
            node_table,
            bit_table,
            device,
        ),
    }
    model.load_state_dict(float_model_state)
    readout.load_state_dict(float_readout_state)

    model_parameters = sum(value.numel() for value in model.parameters())
    readout_parameters = sum(value.numel() for value in readout.parameters())
    receipt = {
        "schema": "butterfly112_prefix_readout_shadow_v1",
        "configuration": vars(args) | {
            "state_trace": str(args.state_trace),
            "butterfly_model": str(args.butterfly_model),
            "output_dir": str(args.output_dir),
        },
        "splits": {
            "train": [0, train_end],
            "development": [train_end, development_end],
            "holdout": [development_end, holdout_end],
        },
        "float": float_metrics,
        "quantized": quantized_metrics,
        "parameter_accounting": {
            "model_int8_bytes": model_parameters,
            "readout_int8_bytes": readout_parameters,
            "combined_int8_bytes": model_parameters + readout_parameters,
        },
        "contract": {
            "causal_target_alignment": True,
            "readout_trained_on_teacher_states": True,
            "rollout_uses_student_state": True,
            "fake_int8_screen": True,
            "integer_inference_implemented": False,
            "native_archive_evidence": False,
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=False)
    torch.save(readout.state_dict(), args.output_dir / "readout.pt")
    (args.output_dir / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(json.dumps(receipt, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
