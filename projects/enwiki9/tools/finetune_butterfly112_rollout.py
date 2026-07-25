#!/usr/bin/env python3
"""Fine-tune Butterfly-112 on autonomous causal state windows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from train_butterfly112_state_shadow import (
    ButterflyLstm,
    Trace,
    evaluate,
    evaluate_rollout,
    fake_int8,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--input-model", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--input-rank", type=int, required=True)
    parser.add_argument("--event-rank", type=int, required=True)
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--window", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=5e-4)
    parser.add_argument("--cell-weight", type=float, default=0.25)
    parser.add_argument("--development-rows", type=int, default=16384)
    parser.add_argument("--rollout-rows", type=int, default=4096)
    parser.add_argument("--threads", type=int, default=6)
    parser.add_argument("--seed", type=int, default=112)
    args = parser.parse_args()

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(args.threads)
    device = torch.device("cpu")
    trace = Trace(args.trace)
    split = int(trace.rows * 0.9)
    if split <= args.window:
        raise ValueError("trace is too short for rollout windows")

    model = ButterflyLstm(
        trace.inputs, trace.cells, args.input_rank, args.event_rank
    ).to(device)
    model.load_state_dict(
        torch.load(args.input_model, map_location=device, weights_only=True)
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    rng = np.random.default_rng(args.seed)

    model.train()
    last_loss = None
    for step in range(args.steps):
        starts = rng.integers(
            0, split - args.window, size=args.batch_size, dtype=np.int64
        )
        indices = (
            starts[:, None] + np.arange(args.window, dtype=np.int64)[None, :]
        )
        flat = trace.batch(indices.reshape(-1), device)
        shaped = [
            value.reshape(args.batch_size, args.window, -1) for value in flat
        ]
        x, event, hidden0, cell0, target_hidden, target_cell = shaped
        event = event.reshape(args.batch_size, args.window)
        hidden = hidden0[:, 0]
        cell = cell0[:, 0]
        hidden_loss = torch.zeros((), device=device)
        cell_loss = torch.zeros((), device=device)
        for offset in range(args.window):
            hidden, cell = model(
                x[:, offset], event[:, offset], hidden, cell
            )
            hidden_loss = hidden_loss + torch.mean(
                torch.square(hidden - target_hidden[:, offset])
            )
            cell_loss = cell_loss + torch.mean(
                torch.square(cell - target_cell[:, offset])
            )
        loss = (
            hidden_loss + args.cell_weight * cell_loss
        ) / args.window
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        last_loss = float(loss.detach())
        if (step + 1) % 100 == 0:
            print(
                json.dumps({"step": step + 1, "loss": last_loss}), flush=True
            )

    development_rows = min(args.development_rows, trace.rows - split)
    dev_indices = np.linspace(
        split, trace.rows - 1, development_rows, dtype=np.int64
    )
    model.eval()
    float_metrics = evaluate(
        model, trace, dev_indices, args.batch_size, device
    )
    float_rollout = evaluate_rollout(
        model, trace, split, args.rollout_rows, device
    )
    float_state = {
        name: value.clone() for name, value in model.state_dict().items()
    }
    model.load_state_dict(fake_int8(model))
    int8_metrics = evaluate(
        model, trace, dev_indices, args.batch_size, device
    )
    int8_rollout = evaluate_rollout(
        model, trace, split, args.rollout_rows, device
    )
    model.load_state_dict(float_state)

    parameters = sum(value.numel() for value in model.parameters())
    receipt = {
        "schema": "butterfly112_rollout_finetune_v1",
        "configuration": {
            key: str(value) if isinstance(value, Path) else value
            for key, value in vars(args).items()
        },
        "training_final_loss": last_loss,
        "float": {
            "one_step": float_metrics,
            "rollout": float_rollout,
        },
        "fake_int8": {
            "one_step": int8_metrics,
            "rollout": int8_rollout,
        },
        "parameter_accounting": {
            "parameters": parameters,
            "int8_bytes": parameters,
        },
        "contract": {
            "student_state_carried_within_window": True,
            "teacher_state_used_only_for_window_initialization_and_loss": True,
            "integer_inference_implemented": False,
            "native_archive_evidence": False,
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=False)
    torch.save(model.state_dict(), args.output_dir / "model.pt")
    (args.output_dir / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
