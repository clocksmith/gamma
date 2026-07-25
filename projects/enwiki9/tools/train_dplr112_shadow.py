#!/usr/bin/env python3
"""Train and screen a quantized DPLR replacement for both endpoint LSTMs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import struct
import time
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F


TRACE_HEADER = struct.Struct("<8sIIIIQ")
TRACE_MAGIC = b"DPLRTRC1"
TRACE_DTYPE = np.dtype(
    [
        ("compact_base_p1", "<u2"),
        ("side_lstm_p1", "<u2"),
        ("main_lstm_p1", "<u2"),
        ("final_p1", "<u2"),
        ("bit", "u1"),
    ]
)
TOTAL = 65536.0
LN2 = math.log(2.0)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def read_trace(path: Path) -> tuple[np.memmap, int]:
    with path.open("rb") as source:
        header = source.read(TRACE_HEADER.size)
    if len(header) != TRACE_HEADER.size:
        raise ValueError("truncated DPLR teacher header")
    magic, version, header_bytes, row_bytes, field_mask, rows = (
        TRACE_HEADER.unpack(header)
    )
    if (
        magic != TRACE_MAGIC
        or version != 1
        or header_bytes != TRACE_HEADER.size
        or row_bytes != TRACE_DTYPE.itemsize
        or field_mask != 15
        or rows <= 0
        or rows % 8
    ):
        raise ValueError("invalid DPLR teacher contract")
    if path.stat().st_size != TRACE_HEADER.size + rows * TRACE_DTYPE.itemsize:
        raise ValueError("DPLR teacher size does not match row count")
    trace = np.memmap(
        path,
        mode="r",
        dtype=TRACE_DTYPE,
        offset=TRACE_HEADER.size,
        shape=(rows,),
    )
    return trace, rows


def read_wrt_store(path: Path, expected_bytes: int) -> np.ndarray:
    data = np.fromfile(path, dtype=np.uint8)
    if len(data) != expected_bytes + 5:
        raise ValueError("WRT store size does not match teacher rows")
    return data[5:].copy()


def tree_nodes(bits: np.ndarray) -> np.ndarray:
    result = np.empty(bits.shape, dtype=np.int64)
    prefix = np.zeros(bits.shape[0], dtype=np.int64)
    for position in range(8):
        result[:, position] = (1 << position) - 1 + prefix
        prefix = (prefix << 1) | bits[:, position]
    return result


class DplrCell(nn.Module):
    def __init__(
        self,
        *,
        models: int,
        cells: int,
        rank: int,
        event_rank: int,
        readout_rank: int,
    ) -> None:
        super().__init__()
        self.models = models
        self.cells = cells
        self.rank = rank
        self.event_rank = event_rank
        self.readout_rank = readout_rank
        self.projection = nn.Parameter(torch.empty(models, rank, cells))
        self.gate_expansion = nn.Parameter(
            torch.empty(models, 4, cells, rank)
        )
        self.diagonal = nn.Parameter(torch.empty(models, 4, cells))
        self.event_embedding = nn.Parameter(
            torch.empty(models, 256, event_rank)
        )
        self.event_expansion = nn.Parameter(
            torch.empty(models, 4, cells, event_rank)
        )
        self.gate_bias = nn.Parameter(torch.zeros(models, 4, cells))
        self.readout_projection = nn.Parameter(
            torch.empty(models, readout_rank, cells)
        )
        self.node_weight = nn.Parameter(
            torch.empty(models, 255, readout_rank)
        )
        self.node_bias = nn.Parameter(torch.zeros(models, 255))
        self.reset_parameters()

    def reset_parameters(self) -> None:
        for parameter in (
            self.projection,
            self.gate_expansion,
            self.event_embedding,
            self.event_expansion,
            self.readout_projection,
            self.node_weight,
        ):
            nn.init.normal_(parameter, mean=0.0, std=0.03)
        nn.init.constant_(self.diagonal, 0.0)
        with torch.no_grad():
            self.gate_bias[:, 1, :].fill_(1.5)

    def initial_state(
        self, batch: int, device: torch.device
    ) -> tuple[torch.Tensor, torch.Tensor]:
        shape = (batch, self.models, self.cells)
        return (
            torch.zeros(shape, device=device),
            torch.zeros(shape, device=device),
        )

    def advance(
        self,
        previous_byte: torch.Tensor,
        hidden: torch.Tensor,
        cell: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        projected = torch.einsum(
            "bmn,mrn->bmr", hidden, self.projection
        )
        recurrent = torch.einsum(
            "bmr,mgnr->bmgn", projected, self.gate_expansion
        )
        event = self.event_embedding[:, previous_byte, :].permute(1, 0, 2)
        event_term = torch.einsum(
            "bme,mgne->bmgn", event, self.event_expansion
        )
        gates = (
            recurrent
            + event_term
            + hidden[:, :, None, :] * self.diagonal[None, :, :, :]
            + self.gate_bias[None, :, :, :]
        )
        input_gate = torch.sigmoid(gates[:, :, 0, :])
        forget_gate = torch.sigmoid(gates[:, :, 1, :])
        output_gate = torch.sigmoid(gates[:, :, 2, :])
        candidate = torch.tanh(gates[:, :, 3, :])
        cell = forget_gate * cell + input_gate * candidate
        hidden = output_gate * torch.tanh(cell)
        return hidden, cell

    def readout(
        self, hidden: torch.Tensor, nodes: torch.Tensor
    ) -> torch.Tensor:
        projected = torch.einsum(
            "bmn,mkn->bmk", hidden, self.readout_projection
        )
        outputs = []
        for position in range(8):
            node = nodes[:, position]
            weight = self.node_weight[:, node, :].permute(1, 0, 2)
            bias = self.node_bias[:, node].permute(1, 0)
            outputs.append((projected * weight).sum(dim=-1) + bias)
        return torch.stack(outputs, dim=-1)


def quantize_state(
    model: nn.Module,
) -> tuple[dict[str, torch.Tensor], dict[str, np.ndarray], int]:
    dequantized: dict[str, torch.Tensor] = {}
    payload: dict[str, np.ndarray] = {}
    parameter_bytes = 0
    for name, value in model.state_dict().items():
        maximum = float(value.abs().max())
        scale = maximum / 127.0 if maximum > 0.0 else 1.0
        quantized = torch.clamp(torch.round(value / scale), -127, 127).to(
            torch.int8
        )
        dequantized[name] = quantized.float() * scale
        payload[name + ".q"] = quantized.cpu().numpy()
        payload[name + ".scale"] = np.asarray(scale, dtype=np.float32)
        parameter_bytes += quantized.numel() + 4
    return dequantized, payload, parameter_bytes


def load_arrays(
    trace_path: Path, wrt_store_path: Path
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    trace, rows = read_trace(trace_path)
    byte_count = rows // 8
    bits = np.asarray(trace["bit"], dtype=np.uint8).reshape(byte_count, 8)
    if np.any(bits > 1):
        raise ValueError("teacher trace contains invalid truth bits")
    wrt = read_wrt_store(wrt_store_path, byte_count)
    if not np.array_equal(np.packbits(bits, axis=1).reshape(-1), wrt):
        raise ValueError("teacher truth bits do not reconstruct WRT store")
    main = (
        np.asarray(trace["main_lstm_p1"], dtype=np.float32)
        .reshape(byte_count, 8)
        / TOTAL
    )
    side = (
        np.asarray(trace["side_lstm_p1"], dtype=np.float32)
        .reshape(byte_count, 8)
        / TOTAL
    )
    targets = np.stack((main, side), axis=1)
    nodes = tree_nodes(bits)
    return wrt, bits, nodes, targets


def window_batch(
    *,
    wrt: np.ndarray,
    bits: np.ndarray,
    nodes: np.ndarray,
    targets: np.ndarray,
    starts: np.ndarray,
    sequence: int,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    offsets = np.arange(sequence, dtype=np.int64)
    indexes = starts[:, None] + offsets[None, :]
    previous = np.maximum(indexes - 1, 0)
    return (
        torch.from_numpy(wrt[previous].astype(np.int64)).to(device),
        torch.from_numpy(bits[indexes].astype(np.float32)).to(device),
        torch.from_numpy(nodes[indexes]).to(device),
        torch.from_numpy(targets[indexes]).to(device),
    )


def batch_loss(
    model: DplrCell,
    previous: torch.Tensor,
    bits: torch.Tensor,
    nodes: torch.Tensor,
    targets: torch.Tensor,
    actual_weight: float,
) -> torch.Tensor:
    batch, sequence = previous.shape
    hidden, cell = model.initial_state(batch, previous.device)
    total = torch.zeros((), device=previous.device)
    for position in range(sequence):
        hidden, cell = model.advance(previous[:, position], hidden, cell)
        logits = model.readout(hidden, nodes[:, position])
        teacher_loss = F.binary_cross_entropy_with_logits(
            logits, targets[:, position], reduction="mean"
        )
        actual = bits[:, position, None, :].expand(-1, model.models, -1)
        actual_loss = F.binary_cross_entropy_with_logits(
            logits, actual, reduction="mean"
        )
        total = total + teacher_loss + actual_weight * actual_loss
    return total / sequence


@torch.no_grad()
def evaluate(
    *,
    model: DplrCell,
    wrt: np.ndarray,
    bits: np.ndarray,
    nodes: np.ndarray,
    targets: np.ndarray,
    start: int,
    end: int,
    sequence: int,
    batch_size: int,
    device: torch.device,
) -> dict[str, Any]:
    starts = np.arange(start, end - sequence + 1, sequence, dtype=np.int64)
    student_bits = np.zeros(2, dtype=np.float64)
    teacher_bits = np.zeros(2, dtype=np.float64)
    distillation_bits = np.zeros(2, dtype=np.float64)
    evaluated_bytes = 0
    for offset in range(0, len(starts), batch_size):
        part = starts[offset : offset + batch_size]
        previous, actual, node, target = window_batch(
            wrt=wrt,
            bits=bits,
            nodes=nodes,
            targets=targets,
            starts=part,
            sequence=sequence,
            device=device,
        )
        hidden, cell = model.initial_state(len(part), device)
        for position in range(sequence):
            hidden, cell = model.advance(previous[:, position], hidden, cell)
            logits = model.readout(hidden, node[:, position])
            probability = torch.sigmoid(logits).clamp(1.0 / TOTAL, 1.0 - 1.0 / TOTAL)
            truth = actual[:, position, None, :].expand(-1, 2, -1)
            student = -torch.where(
                truth > 0.5, torch.log2(probability), torch.log2(1.0 - probability)
            )
            teacher_probability = target[:, position].clamp(
                1.0 / TOTAL, 1.0 - 1.0 / TOTAL
            )
            teacher = -torch.where(
                truth > 0.5,
                torch.log2(teacher_probability),
                torch.log2(1.0 - teacher_probability),
            )
            entropy = -(
                teacher_probability * torch.log2(teacher_probability)
                + (1.0 - teacher_probability)
                * torch.log2(1.0 - teacher_probability)
            )
            cross_entropy = -(
                teacher_probability * torch.log2(probability)
                + (1.0 - teacher_probability) * torch.log2(1.0 - probability)
            )
            student_bits += student.sum(dim=(0, 2)).cpu().numpy()
            teacher_bits += teacher.sum(dim=(0, 2)).cpu().numpy()
            distillation_bits += (cross_entropy - entropy).sum(
                dim=(0, 2)
            ).cpu().numpy()
        evaluated_bytes += len(part) * sequence
    names = ("main", "side")
    return {
        "evaluated_bytes": evaluated_bytes,
        "models": {
            names[index]: {
                "teacher_actual_bits": float(teacher_bits[index]),
                "student_actual_bits": float(student_bits[index]),
                "student_minus_teacher_bits": float(
                    student_bits[index] - teacher_bits[index]
                ),
                "teacher_kl_bits": float(distillation_bits[index]),
                "student_bits_per_byte": float(
                    student_bits[index] / evaluated_bytes
                ),
            }
            for index in range(2)
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--wrt-store", required=True, type=Path)
    parser.add_argument("--rank", required=True, type=int, choices=(1, 2, 4))
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--steps", type=int, default=800)
    parser.add_argument("--sequence", type=int, default=64)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--cells", type=int, default=112)
    parser.add_argument("--event-rank", type=int, default=4)
    parser.add_argument("--readout-rank", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=0.002)
    parser.add_argument("--actual-weight", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=428112)
    parser.add_argument("--threads", type=int, default=16)
    args = parser.parse_args()
    if args.steps <= 0 or args.sequence <= 0 or args.batch_size <= 0:
        raise ValueError("steps, sequence, and batch size must be positive")

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(args.threads)
    torch.use_deterministic_algorithms(True)
    device = torch.device("cpu")

    wrt, bits, nodes, targets = load_arrays(args.trace, args.wrt_store)
    byte_count = len(wrt)
    train_end = int(byte_count * 0.60)
    development_end = int(byte_count * 0.80)
    if train_end <= args.sequence + 1:
        raise ValueError("training split is too small")

    model = DplrCell(
        models=2,
        cells=args.cells,
        rank=args.rank,
        event_rank=args.event_rank,
        readout_rank=args.readout_rank,
    ).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate)
    rng = np.random.default_rng(args.seed)
    history: list[dict[str, float]] = []
    started = time.perf_counter()
    for step in range(1, args.steps + 1):
        starts = rng.integers(
            1,
            train_end - args.sequence,
            size=args.batch_size,
            dtype=np.int64,
        )
        previous, actual, node, target = window_batch(
            wrt=wrt,
            bits=bits,
            nodes=nodes,
            targets=targets,
            starts=starts,
            sequence=args.sequence,
            device=device,
        )
        optimizer.zero_grad(set_to_none=True)
        loss = batch_loss(
            model, previous, actual, node, target, args.actual_weight
        )
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        if step == 1 or step % 100 == 0 or step == args.steps:
            record = {
                "step": step,
                "loss_nats": float(loss.detach()),
                "elapsed_seconds": time.perf_counter() - started,
            }
            history.append(record)
            print(json.dumps(record), flush=True)

    float_development = evaluate(
        model=model,
        wrt=wrt,
        bits=bits,
        nodes=nodes,
        targets=targets,
        start=train_end,
        end=development_end,
        sequence=args.sequence,
        batch_size=args.batch_size,
        device=device,
    )
    float_holdout = evaluate(
        model=model,
        wrt=wrt,
        bits=bits,
        nodes=nodes,
        targets=targets,
        start=development_end,
        end=byte_count,
        sequence=args.sequence,
        batch_size=args.batch_size,
        device=device,
    )

    dequantized, payload, parameter_bytes = quantize_state(model)
    quantized_model = DplrCell(
        models=2,
        cells=args.cells,
        rank=args.rank,
        event_rank=args.event_rank,
        readout_rank=args.readout_rank,
    ).to(device)
    quantized_model.load_state_dict(dequantized)
    quantized_development = evaluate(
        model=quantized_model,
        wrt=wrt,
        bits=bits,
        nodes=nodes,
        targets=targets,
        start=train_end,
        end=development_end,
        sequence=args.sequence,
        batch_size=args.batch_size,
        device=device,
    )
    quantized_holdout = evaluate(
        model=quantized_model,
        wrt=wrt,
        bits=bits,
        nodes=nodes,
        targets=targets,
        start=development_end,
        end=byte_count,
        sequence=args.sequence,
        batch_size=args.batch_size,
        device=device,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    parameter_path = args.output_dir / "parameters_int8.npz"
    np.savez_compressed(parameter_path, **payload)
    receipt = {
        "schema": "dplr112_shadow_training_v1",
        "contract": {
            "causal": True,
            "teacher_hidden_state_used": False,
            "teacher_outputs": ["main_lstm_p1", "side_lstm_p1"],
            "state_reset_each_evaluation_window": True,
            "integer_inference_implemented": False,
            "quantized_screen_uses_dequantized_int8_parameters": True,
            "native_archive_evidence": False,
        },
        "configuration": {
            "rank": args.rank,
            "cells": args.cells,
            "event_rank": args.event_rank,
            "readout_rank": args.readout_rank,
            "steps": args.steps,
            "sequence": args.sequence,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate,
            "actual_weight": args.actual_weight,
            "seed": args.seed,
            "threads": args.threads,
        },
        "inputs": {
            "trace": artifact(args.trace),
            "wrt_store": artifact(args.wrt_store),
            "wrt_bytes": byte_count,
        },
        "splits": {
            "train": [0, train_end],
            "development": [train_end, development_end],
            "holdout": [development_end, byte_count],
        },
        "training": {
            "elapsed_seconds": time.perf_counter() - started,
            "history": history,
        },
        "parameter_accounting": {
            "tensor_count": len(payload) // 2,
            "int8_plus_scale_bytes": parameter_bytes,
            "compressed_npz": artifact(parameter_path),
        },
        "float": {
            "development": float_development,
            "holdout": float_holdout,
        },
        "quantized": {
            "development": quantized_development,
            "holdout": quantized_holdout,
        },
    }
    receipt_path = args.output_dir / "receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "receipt": str(receipt_path.resolve()),
                "parameter_bytes": parameter_bytes,
                "compressed_parameter_bytes": parameter_path.stat().st_size,
                "quantized_holdout": quantized_holdout,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
