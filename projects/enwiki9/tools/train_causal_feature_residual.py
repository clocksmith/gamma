#!/usr/bin/env python3
"""Compile endpoint428 final-minus-base logits from cheap causal features."""

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

from train_dplr112_readout_shadow import TeacherTrace, coding_metrics
from train_dplr112_state_shadow import StateTrace


class FeatureResidual(nn.Module):
    def __init__(self, inputs, rank, event_rank):
        super().__init__()
        self.projection = nn.Parameter(torch.empty(rank, inputs))
        self.event = nn.Embedding(256, event_rank)
        self.node_weight = nn.Parameter(torch.empty(255, rank + event_rank))
        self.node_bias = nn.Parameter(torch.zeros(255))
        nn.init.normal_(self.projection, std=0.02)
        nn.init.normal_(self.event.weight, std=0.02)
        nn.init.zeros_(self.node_weight)

    def forward(self, features, symbol, nodes, base_probability):
        projected = features @ self.projection.t()
        representation = torch.cat((projected, self.event(symbol)), dim=1)
        residual = torch.sum(
            self.node_weight[nodes] * representation[:, None, :], dim=2
        )
        residual = residual + self.node_bias[nodes]
        base = base_probability.clamp(1e-6, 1.0 - 1e-6)
        base_logit = torch.log(base) - torch.log1p(-base)
        return base_logit + residual


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


def batch(state, teacher, indices):
    features, symbol, _, _, _, _ = state.take(indices)
    target, bits, nodes = teacher.take_bytes(indices + 1)
    row_indices = (
        (indices + 1)[:, None] * 8 + np.arange(8, dtype=np.int64)
    )
    base = teacher.data["base"][row_indices].astype(np.float32) / 65536.0
    return (
        torch.from_numpy(np.array(features, copy=True)),
        torch.from_numpy(np.array(symbol, copy=True)).long(),
        torch.from_numpy(nodes),
        torch.from_numpy(base),
        torch.from_numpy(target),
        torch.from_numpy(bits),
    )


def evaluate(model, state, teacher, start, stop, batch_size):
    totals = {
        "teacher_actual_bits": 0.0,
        "student_actual_bits": 0.0,
        "student_minus_teacher_actual_bits": 0.0,
        "teacher_kl_bits": 0.0,
    }
    base_actual = 0.0
    model.eval()
    with torch.no_grad():
        for left in range(start, stop, batch_size):
            right = min(left + batch_size, stop)
            features, symbol, nodes, base, target, bits = batch(
                state, teacher, np.arange(left, right)
            )
            logits = model(features, symbol, nodes, base)
            metrics = coding_metrics(logits, target, bits)
            base_logits = torch.log(base.clamp(1e-7, 1 - 1e-7)) - torch.log1p(
                -base.clamp(1e-7, 1 - 1e-7)
            )
            base_actual += coding_metrics(base_logits, target, bits)[
                "student_actual_bits"
            ]
            for key, value in metrics.items():
                totals[key] += value
    totals["bytes"] = stop - start
    totals["base_actual_bits"] = base_actual
    totals["student_delta_vs_base_bits"] = totals["student_actual_bits"] - base_actual
    totals["student_bits_per_byte"] = totals["student_actual_bits"] / (stop - start)
    return totals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-trace", required=True)
    parser.add_argument("--teacher-trace", required=True)
    parser.add_argument("--rank", type=int, choices=(1, 2, 4, 8, 16, 32), required=True)
    parser.add_argument("--event-rank", type=int, default=4)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--steps", type=int, default=3000)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--learning-rate", type=float, default=0.003)
    parser.add_argument("--actual-weight", type=float, default=0.25)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--seed", type=int, default=428112)
    args = parser.parse_args()

    torch.set_num_threads(args.threads)
    torch.manual_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    state = StateTrace(args.state_trace)
    teacher = TeacherTrace(args.teacher_trace, "final")
    usable_rows = min(state.rows, teacher.bytes - 1)
    train_stop = int(usable_rows * 0.70)
    dev_stop = int(usable_rows * 0.85)
    model = FeatureResidual(state.inputs, args.rank, args.event_rank)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    history = []
    started = time.monotonic()

    model.train()
    for step in range(1, args.steps + 1):
        indices = rng.integers(0, train_stop, size=args.batch_size)
        features, symbol, nodes, base, target, bits = batch(
            state, teacher, indices
        )
        logits = model(features, symbol, nodes, base)
        soft_loss = nn.functional.binary_cross_entropy_with_logits(logits, target)
        actual_loss = nn.functional.binary_cross_entropy_with_logits(
            logits, bits.float()
        )
        loss = soft_loss + args.actual_weight * actual_loss
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        if step == 1 or step % 100 == 0 or step == args.steps:
            row = {
                "step": step,
                "loss_nats": float(loss.detach()),
                "soft_loss_nats": float(soft_loss.detach()),
                "actual_loss_nats": float(actual_loss.detach()),
                "elapsed_seconds": time.monotonic() - started,
            }
            history.append(row)
            print(json.dumps(row), flush=True)

    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    float_metrics = {
        "development": evaluate(
            model, state, teacher, train_stop, dev_stop, args.batch_size
        ),
        "holdout": evaluate(
            model, state, teacher, dev_stop, usable_rows, args.batch_size
        ),
    }
    packed, restored, raw_bytes = quantize(model)
    parameter_path = output / "parameters_int8.npz"
    np.savez_compressed(parameter_path, **packed)
    quantized = FeatureResidual(state.inputs, args.rank, args.event_rank)
    quantized.load_state_dict(restored)
    quantized_metrics = {
        "development": evaluate(
            quantized, state, teacher, train_stop, dev_stop, args.batch_size
        ),
        "holdout": evaluate(
            quantized, state, teacher, dev_stop, usable_rows, args.batch_size
        ),
    }
    receipt = {
        "schema": "causal_feature_residual_compiler_v1",
        "configuration": vars(args),
        "splits": {
            "train": [0, train_stop],
            "development": [train_stop, dev_stop],
            "holdout": [dev_stop, usable_rows],
            "target_shift_bytes": 1,
        },
        "training": {
            "elapsed_seconds": time.monotonic() - started,
            "history": history,
        },
        "float": float_metrics,
        "quantized": quantized_metrics,
        "parameter_accounting": {
            "int8_plus_scale_bytes": raw_bytes,
            "compressed_npz_bytes": parameter_path.stat().st_size,
            "compressed_npz_sha256": sha256(parameter_path),
        },
        "contract": {
            "causal_features": True,
            "teacher_hidden_or_cell_used": False,
            "sealed_holdout_not_used_for_training": True,
            "quantized_screen_uses_dequantized_int8_parameters": True,
            "integer_inference_implemented": False,
            "native_archive_evidence": False,
        },
    }
    receipt_path = output / "receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"receipt": str(receipt_path), "quantized": quantized_metrics}))


if __name__ == "__main__":
    main()
