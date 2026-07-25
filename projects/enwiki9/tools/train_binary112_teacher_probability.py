#!/usr/bin/env python3
"""Distill exact branch probabilities through a binary 205-way softmax."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import torch
from torch import nn

from finetune_butterfly112_teacher_probability import teacher_arrays
from train_binary112_state_shadow import (
    BinaryLstm112,
    binary_ste,
    load_one_layer_snapshot,
)
from train_butterfly112_readout_shadow import prefix_tables
from train_butterfly112_state_shadow import Trace


def low_bit_ste(weights, bits):
    if bits == 32:
        return weights
    if bits == 1:
        return binary_ste(weights)
    maximum = (1 << (bits - 1)) - 1
    scale = torch.amax(torch.abs(weights), dim=-1, keepdim=True) / maximum
    scale = scale.clamp_min(1.0e-8)
    quantized = (
        torch.round(weights / scale).clamp(-maximum, maximum) * scale
    )
    return weights + (quantized - weights).detach()


def prefix_masks(outputs, device):
    node = np.zeros((255, outputs), dtype=np.float32)
    right = np.zeros((255, outputs), dtype=np.float32)
    for value in range(outputs):
        current = 0
        for shift in range(7, -1, -1):
            bit = (value >> shift) & 1
            node[current, value] = 1.0
            if bit:
                right[current, value] = 1.0
            current = 2 * current + 1 + bit
    return torch.from_numpy(node).to(device), torch.from_numpy(right).to(device)


class BinaryBranch(nn.Module):
    def __init__(self, snapshot, output_bits):
        super().__init__()
        self.recurrent = BinaryLstm112(snapshot)
        self.output_bits = output_bits
        self.output_weights = nn.Parameter(
            torch.from_numpy(snapshot["output"].copy())
        )

    def advance(self, x, event, hidden, cell):
        return self.recurrent(x, event, hidden, cell)

    def prefix_probability(
        self, hidden, target_bytes, target_nodes, node_mask, right_mask
    ):
        augmented = torch.cat(
            (hidden, torch.ones_like(hidden[:, :1])), dim=1
        )
        logits = augmented @ low_bit_ste(
            self.output_weights, self.output_bits
        ).T
        distribution = torch.softmax(logits, dim=1)
        denominator = distribution @ node_mask.T
        numerator = distribution @ right_mask.T
        probability = numerator / denominator.clamp_min(1.0e-12)
        nodes = target_nodes.index_select(0, target_bytes)
        return probability.gather(1, nodes).clamp(1.0e-6, 1.0 - 1.0e-6)

    def parameter_bytes(self):
        recurrent = self.recurrent.parameter_bytes()
        rows = self.output_weights.shape[0]
        packed = (
            self.output_weights.numel() * self.output_bits + 7
        ) // 8
        scales = rows * 2
        recurrent["quantized_output_weight_bytes"] = packed
        recurrent["output_weight_bits"] = self.output_bits
        recurrent["fp16_output_scale_bytes"] = scales
        recurrent["total_bytes"] += packed + scales
        return recurrent


@torch.no_grad()
def evaluate(
    model,
    trace,
    teacher_probability,
    truth_bits,
    truth_bytes,
    indices,
    target_nodes,
    node_mask,
    right_mask,
    device,
    rollout,
):
    student_actual = 0.0
    teacher_actual = 0.0
    teacher_kl = 0.0
    if rollout:
        first = trace.batch(np.asarray([indices[0]]), device)
        hidden = first[2]
        cell = first[3]
    for index in indices:
        batch = trace.batch(np.asarray([index]), device)
        if not rollout:
            hidden, cell = batch[2], batch[3]
        hidden, cell = model.advance(
            batch[0], batch[1], hidden, cell
        )
        target_index = index + 1
        target = torch.tensor(
            [int(truth_bytes[target_index])], dtype=torch.long, device=device
        )
        student = (
            model.prefix_probability(
                hidden,
                target,
                target_nodes,
                node_mask,
                right_mask,
            )[0]
            .cpu()
            .numpy()
        )
        teacher = np.clip(
            teacher_probability[target_index], 1.0e-6, 1.0 - 1.0e-6
        )
        truth = truth_bits[target_index]
        student_actual += float(
            -(truth * np.log2(student) + (1.0 - truth) * np.log2(1.0 - student)).sum()
        )
        teacher_actual += float(
            -(truth * np.log2(teacher) + (1.0 - truth) * np.log2(1.0 - teacher)).sum()
        )
        teacher_kl += float(
            (
                teacher * np.log2(teacher / student)
                + (1.0 - teacher)
                * np.log2((1.0 - teacher) / (1.0 - student))
            ).sum()
        )
    rows = len(indices)
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
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--input-state-model", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=3000)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--state-weight", type=float, default=0.5)
    parser.add_argument(
        "--output-bits", type=int, choices=(1, 4, 32), default=1
    )
    parser.add_argument("--cell-weight", type=float, default=0.25)
    parser.add_argument("--rollout-rows", type=int, default=4096)
    parser.add_argument("--threads", type=int, default=6)
    parser.add_argument("--seed", type=int, default=112)
    args = parser.parse_args()

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(args.threads)
    device = torch.device("cpu")
    trace = Trace(args.trace)
    snapshot = load_one_layer_snapshot(args.snapshot)
    teacher_probability, truth_bits, truth_bytes = teacher_arrays(
        args.teacher_trace, args.branch
    )
    model = BinaryBranch(snapshot, args.output_bits).to(device)
    model.recurrent.load_state_dict(
        torch.load(
            args.input_state_model, map_location=device, weights_only=True
        )
    )
    target_nodes, _ = prefix_tables(device)
    node_mask, right_mask = prefix_masks(snapshot["outputs"], device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    rng = np.random.default_rng(args.seed)
    train_end = 84000

    model.train()
    last = None
    for step in range(args.steps):
        indices = rng.integers(0, train_end, size=args.batch_size)
        batch = trace.batch(indices, device)
        hidden, cell = model.advance(*batch[:4])
        target_indices = indices + 1
        target = torch.from_numpy(
            truth_bytes[target_indices].astype(np.int64)
        ).to(device)
        student = model.prefix_probability(
            hidden, target, target_nodes, node_mask, right_mask
        )
        teacher = torch.from_numpy(
            teacher_probability[target_indices]
        ).to(device)
        distillation_loss = nn.functional.binary_cross_entropy(
            student, teacher
        )
        hidden_loss = torch.mean(torch.square(hidden - batch[4]))
        cell_loss = torch.mean(torch.square(cell - batch[5]))
        state_loss = hidden_loss + args.cell_weight * cell_loss
        loss = distillation_loss + args.state_weight * state_loss
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        last = {
            "loss": float(loss.detach()),
            "distillation_loss": float(distillation_loss.detach()),
            "state_loss": float(state_loss.detach()),
        }
        if (step + 1) % 250 == 0:
            print(json.dumps({"step": step + 1} | last), flush=True)

    model.eval()
    holdout = np.arange(102000, 120000, dtype=np.int64)
    rollout_indices = np.arange(
        102000, 102000 + args.rollout_rows, dtype=np.int64
    )
    receipt = {
        "schema": "binary112_teacher_probability_v1",
        "configuration": {
            key: str(value) if isinstance(value, Path) else value
            for key, value in vars(args).items()
        },
        "training_final": last,
        "one_step_holdout": evaluate(
            model,
            trace,
            teacher_probability,
            truth_bits,
            truth_bytes,
            holdout,
            target_nodes,
            node_mask,
            right_mask,
            device,
            False,
        ),
        "rollout_holdout": evaluate(
            model,
            trace,
            teacher_probability,
            truth_bits,
            truth_bytes,
            rollout_indices,
            target_nodes,
            node_mask,
            right_mask,
            device,
            True,
        ),
        "parameter_accounting": model.parameter_bytes(),
        "contract": {
            "binary_recurrent_weights": True,
            "output_weight_bits": args.output_bits,
            "exact_205_way_softmax_and_prefix_conditioning": True,
            "soft_target_is_exact_teacher_branch_probability": True,
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
