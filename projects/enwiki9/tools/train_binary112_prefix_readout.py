#!/usr/bin/env python3
"""Train a compact prefix readout on a binary recurrent student."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn

from train_binary112_state_shadow import (
    BinaryLstm112,
    load_one_layer_snapshot,
)
from train_dplr112_readout_shadow import (
    PrefixReadout,
    TeacherTrace,
    coding_metrics,
    quantize,
)
from train_butterfly112_state_shadow import Trace


@torch.no_grad()
def evaluate(
    model, readout, state_trace, teacher_trace, start, stop, batch_size
):
    totals = {
        "teacher_actual_bits": 0.0,
        "student_actual_bits": 0.0,
        "student_minus_teacher_actual_bits": 0.0,
        "teacher_kl_bits": 0.0,
    }
    for left in range(start, stop, batch_size):
        right = min(left + batch_size, stop)
        indices = np.arange(left, right)
        batch = state_trace.batch(indices, torch.device("cpu"))
        hidden, _ = model(*batch[:4])
        probability, bits, nodes = teacher_trace.take_bytes(indices + 1)
        metrics = coding_metrics(
            readout(hidden, torch.from_numpy(nodes)),
            torch.from_numpy(probability),
            torch.from_numpy(bits),
        )
        for key, value in metrics.items():
            totals[key] += value
    totals["bytes"] = stop - start
    totals["student_bits_per_byte"] = totals["student_actual_bits"] / (
        stop - start
    )
    return totals


@torch.no_grad()
def evaluate_rollout(
    model, readout, state_trace, teacher_trace, start, rows
):
    first = state_trace.batch(np.asarray([start]), torch.device("cpu"))
    hidden, cell = first[2], first[3]
    totals = {
        "teacher_actual_bits": 0.0,
        "student_actual_bits": 0.0,
        "student_minus_teacher_actual_bits": 0.0,
        "teacher_kl_bits": 0.0,
    }
    for index in range(start, start + rows):
        batch = state_trace.batch(
            np.asarray([index]), torch.device("cpu")
        )
        hidden, cell = model(batch[0], batch[1], hidden, cell)
        probability, bits, nodes = teacher_trace.take_bytes(
            np.asarray([index + 1])
        )
        metrics = coding_metrics(
            readout(hidden, torch.from_numpy(nodes)),
            torch.from_numpy(probability),
            torch.from_numpy(bits),
        )
        for key, value in metrics.items():
            totals[key] += value
    totals["bytes"] = rows
    totals["student_bits_per_byte"] = totals["student_actual_bits"] / rows
    return totals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-trace", type=Path, required=True)
    parser.add_argument("--teacher-trace", type=Path, required=True)
    parser.add_argument("--branch", choices=("main", "side"), required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--input-state-model", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--readout-rank", type=int, default=16)
    parser.add_argument(
        "--input-node-bits", type=int, choices=(1, 2), default=1
    )
    parser.add_argument(
        "--other-gate-bits", type=int, choices=(1, 2), default=1
    )
    parser.add_argument("--steps", type=int, default=3000)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--state-weight", type=float, default=0.25)
    parser.add_argument("--cell-weight", type=float, default=0.25)
    parser.add_argument("--rollout-rows", type=int, default=4096)
    parser.add_argument("--threads", type=int, default=6)
    parser.add_argument("--seed", type=int, default=112)
    args = parser.parse_args()

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(args.threads)
    device = torch.device("cpu")
    state_trace = Trace(args.state_trace)
    teacher_trace = TeacherTrace(args.teacher_trace, args.branch)
    snapshot = load_one_layer_snapshot(args.snapshot)
    model = BinaryLstm112(
        snapshot, args.input_node_bits, args.other_gate_bits
    ).to(device)
    model.load_state_dict(
        torch.load(
            args.input_state_model, map_location=device, weights_only=True
        )
    )
    readout = PrefixReadout(state_trace.cells, args.readout_rank).to(device)
    optimizer = torch.optim.AdamW(
        list(model.parameters()) + list(readout.parameters()),
        lr=args.learning_rate,
    )
    rng = np.random.default_rng(args.seed)
    train_end = 84000
    model.train()
    readout.train()
    last = None
    for step in range(args.steps):
        indices = rng.integers(0, train_end, size=args.batch_size)
        batch = state_trace.batch(indices, device)
        hidden, cell = model(*batch[:4])
        probability, _, nodes = teacher_trace.take_bytes(indices + 1)
        logits = readout(hidden, torch.from_numpy(nodes))
        distillation_loss = nn.functional.binary_cross_entropy_with_logits(
            logits, torch.from_numpy(probability)
        )
        hidden_loss = torch.mean(torch.square(hidden - batch[4]))
        cell_loss = torch.mean(torch.square(cell - batch[5]))
        state_loss = hidden_loss + args.cell_weight * cell_loss
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
        if (step + 1) % 250 == 0:
            print(json.dumps({"step": step + 1} | last), flush=True)

    model.eval()
    readout.eval()
    float_metrics = {
        "one_step_holdout": evaluate(
            model,
            readout,
            state_trace,
            teacher_trace,
            102000,
            120000,
            args.batch_size,
        ),
        "rollout_holdout": evaluate_rollout(
            model,
            readout,
            state_trace,
            teacher_trace,
            102000,
            args.rollout_rows,
        ),
    }
    packed, restored, readout_bytes = quantize(readout)
    quantized_readout = PrefixReadout(
        state_trace.cells, args.readout_rank
    )
    quantized_readout.load_state_dict(restored)
    quantized_metrics = {
        "one_step_holdout": evaluate(
            model,
            quantized_readout,
            state_trace,
            teacher_trace,
            102000,
            120000,
            args.batch_size,
        ),
        "rollout_holdout": evaluate_rollout(
            model,
            quantized_readout,
            state_trace,
            teacher_trace,
            102000,
            args.rollout_rows,
        ),
    }
    state_bytes = model.parameter_bytes()["total_bytes"]
    receipt = {
        "schema": "binary112_prefix_readout_v1",
        "configuration": {
            key: str(value) if isinstance(value, Path) else value
            for key, value in vars(args).items()
        },
        "training_final": last,
        "float": float_metrics,
        "quantized_readout": quantized_metrics,
        "parameter_accounting": {
            "binary_state_bytes": state_bytes,
            "int8_readout_bytes": readout_bytes,
            "combined_bytes": state_bytes + readout_bytes,
        },
        "contract": {
            "validated_teacher_trace_field_mapping": True,
            "validated_prefix_node_alignment": True,
            "binary_recurrent_weights": True,
            "integer_inference_implemented": False,
            "native_archive_evidence": False,
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=False)
    torch.save(model.state_dict(), args.output_dir / "model.pt")
    np.savez_compressed(args.output_dir / "readout_int8.npz", **packed)
    (args.output_dir / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
