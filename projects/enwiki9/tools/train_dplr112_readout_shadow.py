#!/usr/bin/env python3
"""Fit a counted binary-prefix readout and score DPLR rollout probabilities."""

import argparse
import hashlib
import json
import struct
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

from train_dplr112_state_shadow import DplrTransition, StateTrace, tensors


TEACHER_HEADER = struct.Struct("<8sIIIIQ")
TEACHER_DTYPE = np.dtype(
    [
        ("base", "<u2"),
        ("side", "<u2"),
        ("main", "<u2"),
        ("final", "<u2"),
        ("bit", "u1"),
    ]
)


class TeacherTrace:
    def __init__(self, path, branch):
        self.path = Path(path).resolve()
        with self.path.open("rb") as handle:
            magic, version, header, row, _, rows = TEACHER_HEADER.unpack(
                handle.read(TEACHER_HEADER.size)
            )
        if magic != b"DPLRTRC1" or version != 1 or row != 9 or rows % 8:
            raise ValueError("unsupported teacher trace")
        self.rows = rows
        self.bytes = rows // 8
        self.data = np.memmap(
            self.path, mode="r", dtype=TEACHER_DTYPE, offset=header, shape=(rows,)
        )
        self.branch = branch

    def take_bytes(self, byte_indices):
        row_indices = (
            np.asarray(byte_indices, dtype=np.int64)[:, None] * 8
            + np.arange(8, dtype=np.int64)
        )
        rows = self.data[row_indices]
        probability = rows[self.branch].astype(np.float32) / 65536.0
        bits = rows["bit"].astype(np.int64)
        nodes = np.empty_like(bits)
        prefix = np.zeros(len(byte_indices), dtype=np.int64)
        for position in range(8):
            nodes[:, position] = prefix
            prefix = 2 * prefix + 1 + bits[:, position]
        return probability, bits, nodes


class PrefixReadout(nn.Module):
    def __init__(self, cells, rank):
        super().__init__()
        self.rank = rank
        if rank == 0:
            self.weight = nn.Parameter(torch.empty(255, cells))
        else:
            self.projection = nn.Parameter(torch.empty(rank, cells))
            self.weight = nn.Parameter(torch.empty(255, rank))
            nn.init.normal_(self.projection, std=0.02)
        self.bias = nn.Parameter(torch.zeros(255))
        nn.init.normal_(self.weight, std=0.02)

    def forward(self, hidden, nodes):
        if self.rank:
            hidden = hidden @ self.projection.t()
        selected = self.weight[nodes]
        return torch.sum(selected * hidden[:, None, :], dim=2) + self.bias[nodes]


def load_quantized_dplr(receipt_path, parameter_path):
    receipt = json.loads(Path(receipt_path).read_text())
    config = receipt["configuration"]
    model = DplrTransition(
        receipt["trace"]["inputs"],
        receipt["trace"]["cells"],
        config["rank"],
        config["event_rank"],
    )
    archive = np.load(parameter_path)
    state = {}
    for name in model.state_dict():
        state[name] = torch.from_numpy(
            archive[name].astype(np.float32) * float(archive[name + ".scale"])
        )
    model.load_state_dict(state)
    model.eval()
    return model, receipt


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


def coding_metrics(logits, target_probability, actual_bits):
    probability = torch.sigmoid(logits).clamp(1e-7, 1.0 - 1e-7)
    target = target_probability.clamp(1e-7, 1.0 - 1e-7)
    actual = actual_bits.float()
    inv_log2 = 1.0 / np.log(2.0)
    student_actual = torch.sum(
        -(actual * torch.log(probability) + (1.0 - actual) * torch.log1p(-probability))
    ).item() * inv_log2
    teacher_actual = torch.sum(
        -(actual * torch.log(target) + (1.0 - actual) * torch.log1p(-target))
    ).item() * inv_log2
    teacher_entropy = torch.sum(
        -(target * torch.log(target) + (1.0 - target) * torch.log1p(-target))
    ).item() * inv_log2
    cross_entropy = torch.sum(
        -(target * torch.log(probability) + (1.0 - target) * torch.log1p(-probability))
    ).item() * inv_log2
    return {
        "teacher_actual_bits": teacher_actual,
        "student_actual_bits": student_actual,
        "student_minus_teacher_actual_bits": student_actual - teacher_actual,
        "teacher_kl_bits": cross_entropy - teacher_entropy,
    }


def evaluate_teacher_states(
    readout, state_trace, teacher_trace, start, stop, batch_size
):
    totals = {
        "teacher_actual_bits": 0.0,
        "student_actual_bits": 0.0,
        "student_minus_teacher_actual_bits": 0.0,
        "teacher_kl_bits": 0.0,
    }
    readout.eval()
    with torch.no_grad():
        for left in range(start, stop, batch_size):
            right = min(left + batch_size, stop)
            indices = np.arange(left, right)
            state_batch = state_trace.take(indices)
            hidden = torch.from_numpy(np.array(state_batch[4], copy=True))
            probability, bits, nodes = teacher_trace.take_bytes(indices + 1)
            metrics = coding_metrics(
                readout(hidden, torch.from_numpy(nodes)),
                torch.from_numpy(probability),
                torch.from_numpy(bits),
            )
            for key, value in metrics.items():
                totals[key] += value
    totals["bytes"] = stop - start
    totals["student_bits_per_byte"] = totals["student_actual_bits"] / (stop - start)
    return totals


def evaluate_one_step(
    readout, dplr, state_trace, teacher_trace, start, stop, batch_size
):
    totals = {
        "teacher_actual_bits": 0.0,
        "student_actual_bits": 0.0,
        "student_minus_teacher_actual_bits": 0.0,
        "teacher_kl_bits": 0.0,
    }
    readout.eval()
    dplr.eval()
    with torch.no_grad():
        for left in range(start, stop, batch_size):
            right = min(left + batch_size, stop)
            indices = np.arange(left, right)
            x, symbol, hidden, cell, _, _ = tensors(
                state_trace.take(indices), torch.device("cpu")
            )
            predicted_hidden, _ = dplr(x, symbol.long(), hidden, cell)
            probability, bits, nodes = teacher_trace.take_bytes(indices + 1)
            metrics = coding_metrics(
                readout(predicted_hidden, torch.from_numpy(nodes)),
                torch.from_numpy(probability),
                torch.from_numpy(bits),
            )
            for key, value in metrics.items():
                totals[key] += value
    totals["bytes"] = stop - start
    totals["student_bits_per_byte"] = totals["student_actual_bits"] / (stop - start)
    return totals


def evaluate_rollout(
    readout, dplr, state_trace, teacher_trace, start, rows
):
    stop = min(start + rows, state_trace.rows - 1)
    initial = tensors(state_trace.take(np.array([start])), torch.device("cpu"))
    hidden, cell = initial[2], initial[3]
    totals = {
        "teacher_actual_bits": 0.0,
        "student_actual_bits": 0.0,
        "student_minus_teacher_actual_bits": 0.0,
        "teacher_kl_bits": 0.0,
    }
    with torch.no_grad():
        for index in range(start, stop):
            x, symbol, _, _, _, _ = tensors(
                state_trace.take(np.array([index])), torch.device("cpu")
            )
            hidden, cell = dplr(x, symbol.long(), hidden, cell)
            probability, bits, nodes = teacher_trace.take_bytes(
                np.array([index + 1])
            )
            metrics = coding_metrics(
                readout(hidden, torch.from_numpy(nodes)),
                torch.from_numpy(probability),
                torch.from_numpy(bits),
            )
            for key, value in metrics.items():
                totals[key] += value
    totals["bytes"] = stop - start
    totals["student_bits_per_byte"] = totals["student_actual_bits"] / (stop - start)
    return totals


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-trace", required=True)
    parser.add_argument("--teacher-trace", required=True)
    parser.add_argument("--branch", choices=("main", "side"), required=True)
    parser.add_argument("--dplr-receipt", required=True)
    parser.add_argument("--dplr-parameters", required=True)
    parser.add_argument("--readout-rank", type=int, default=0)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--steps", type=int, default=3000)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--learning-rate", type=float, default=0.003)
    parser.add_argument("--rollout-rows", type=int, default=4096)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--seed", type=int, default=428112)
    args = parser.parse_args()

    torch.set_num_threads(args.threads)
    torch.manual_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    state_trace = StateTrace(args.state_trace)
    teacher_trace = TeacherTrace(args.teacher_trace, args.branch)
    if teacher_trace.bytes <= state_trace.rows:
        raise ValueError("teacher trace lacks one-byte shifted targets")
    dplr, dplr_receipt = load_quantized_dplr(
        args.dplr_receipt, args.dplr_parameters
    )
    readout = PrefixReadout(state_trace.cells, args.readout_rank)
    optimizer = torch.optim.AdamW(readout.parameters(), lr=args.learning_rate)
    train_stop = int(state_trace.rows * 0.70)
    dev_stop = int(state_trace.rows * 0.85)
    started = time.monotonic()
    history = []

    readout.train()
    for step in range(1, args.steps + 1):
        indices = rng.integers(0, train_stop, size=args.batch_size)
        hidden = torch.from_numpy(np.array(state_trace.take(indices)[4], copy=True))
        probability, _, nodes = teacher_trace.take_bytes(indices + 1)
        logits = readout(hidden, torch.from_numpy(nodes))
        target = torch.from_numpy(probability)
        loss = nn.functional.binary_cross_entropy_with_logits(logits, target)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        if step == 1 or step % 100 == 0 or step == args.steps:
            row = {
                "step": step,
                "loss_nats": float(loss.detach()),
                "elapsed_seconds": time.monotonic() - started,
            }
            history.append(row)
            print(json.dumps(row), flush=True)

    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    float_metrics = {
        "teacher_state_holdout": evaluate_teacher_states(
            readout, state_trace, teacher_trace, dev_stop, state_trace.rows, args.batch_size
        ),
        "dplr_one_step_holdout": evaluate_one_step(
            readout, dplr, state_trace, teacher_trace, dev_stop, state_trace.rows, args.batch_size
        ),
        "dplr_rollout_holdout": evaluate_rollout(
            readout, dplr, state_trace, teacher_trace, dev_stop, args.rollout_rows
        ),
    }
    packed, restored, raw_bytes = quantize(readout)
    parameter_path = output / "readout_int8.npz"
    np.savez_compressed(parameter_path, **packed)
    quantized_readout = PrefixReadout(state_trace.cells, args.readout_rank)
    quantized_readout.load_state_dict(restored)
    quantized_metrics = {
        "teacher_state_holdout": evaluate_teacher_states(
            quantized_readout, state_trace, teacher_trace, dev_stop, state_trace.rows, args.batch_size
        ),
        "dplr_one_step_holdout": evaluate_one_step(
            quantized_readout, dplr, state_trace, teacher_trace, dev_stop, state_trace.rows, args.batch_size
        ),
        "dplr_rollout_holdout": evaluate_rollout(
            quantized_readout, dplr, state_trace, teacher_trace, dev_stop, args.rollout_rows
        ),
    }
    receipt = {
        "schema": "dplr112_prefix_readout_shadow_v1",
        "configuration": vars(args),
        "splits": {
            "train": [0, train_stop],
            "development": [train_stop, dev_stop],
            "holdout": [dev_stop, state_trace.rows],
            "teacher_target_shift_bytes": 1,
        },
        "training": {
            "elapsed_seconds": time.monotonic() - started,
            "history": history,
        },
        "float": float_metrics,
        "quantized": quantized_metrics,
        "parameter_accounting": {
            "readout_int8_plus_scale_bytes": raw_bytes,
            "readout_compressed_npz_bytes": parameter_path.stat().st_size,
            "readout_compressed_npz_sha256": sha256(parameter_path),
            "dplr_int8_plus_scale_bytes": dplr_receipt[
                "parameter_accounting"
            ]["int8_plus_scale_bytes"],
            "combined_raw_parameter_bytes": raw_bytes
            + dplr_receipt["parameter_accounting"]["int8_plus_scale_bytes"],
        },
        "contract": {
            "causal_target_alignment": True,
            "readout_trained_on_teacher_states": True,
            "dplr_rollout_uses_student_state": True,
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
