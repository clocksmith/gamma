#!/usr/bin/env python3
"""Distill a slow paired endpoint into a small causal recurrent residual model.

The teacher is used only during offline training.  Replay predictions are built
from the fast endpoint, previously decoded bytes, and the current byte prefix.
Holdout is evaluated once after development-only checkpoint selection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import struct
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset


PAIR_MAGIC = b"CMXAUX1\0"
TARGET_DEBT_BYTES = 681_114


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_inputs(pair_path: Path, store_path: Path) -> tuple[np.ndarray, np.ndarray]:
    raw = pair_path.read_bytes()
    if raw[:8] != PAIR_MAGIC or len(raw) < 16:
        raise ValueError("invalid CMXAUX1 pair trace")
    rows = struct.unpack_from("<Q", raw, 8)[0]
    if rows == 0 or rows % 8 or len(raw) != 16 + rows * 4:
        raise ValueError("invalid pair trace dimensions")
    pair = np.frombuffer(raw, dtype="<u2", offset=16).reshape(rows, 2).copy()
    store_raw = store_path.read_bytes()
    if len(store_raw) != 5 + rows // 8:
        raise ValueError("pair trace and WRT store do not align")
    return pair.reshape(rows // 8, 8, 2), np.frombuffer(store_raw[5:], dtype=np.uint8).copy()


def prefix_contexts(values: np.ndarray) -> np.ndarray:
    result = np.empty((len(values), 8), dtype=np.int64)
    wide = values.astype(np.int64)
    for bit_position in range(8):
        result[:, bit_position] = (1 << bit_position) + (wide >> (8 - bit_position))
    return result


class ChunkDataset(Dataset[tuple[torch.Tensor, ...]]):
    def __init__(
        self,
        values: np.ndarray,
        base_logits: np.ndarray,
        teacher_probabilities: np.ndarray,
        contexts: np.ndarray,
        train_end: int,
        sequence_bytes: int,
        warmup_bytes: int,
    ) -> None:
        self.values = values
        self.base_logits = base_logits
        self.teacher_probabilities = teacher_probabilities
        self.contexts = contexts
        self.sequence_bytes = sequence_bytes
        self.warmup_bytes = warmup_bytes
        self.starts = list(range(warmup_bytes, train_end - sequence_bytes + 1, sequence_bytes))
        if not self.starts:
            raise ValueError("training split is smaller than one sequence")

    def __len__(self) -> int:
        return len(self.starts)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, ...]:
        start = self.starts[index]
        lo = start - self.warmup_bytes
        hi = start + self.sequence_bytes
        previous = np.empty(hi - lo, dtype=np.int64)
        previous[0] = int(self.values[lo - 1]) if lo else 0
        previous[1:] = self.values[lo : hi - 1]
        scored = slice(start, hi)
        return (
            torch.from_numpy(previous),
            torch.from_numpy(self.base_logits[scored]),
            torch.from_numpy(self.teacher_probabilities[scored]),
            torch.from_numpy(self.contexts[scored]),
        )


class SparseGruDistiller(nn.Module):
    def __init__(self, cells: int, embedding_dims: int) -> None:
        super().__init__()
        self.cells = cells
        self.embedding = nn.Embedding(256, embedding_dims)
        self.recurrent = nn.GRU(embedding_dims, cells, batch_first=True)
        self.context_head = nn.Embedding(256, cells)
        self.context_bias = nn.Embedding(256, 1)
        nn.init.zeros_(self.context_head.weight)
        nn.init.zeros_(self.context_bias.weight)

    def forward(
        self,
        previous_bytes: torch.Tensor,
        base_logits: torch.Tensor,
        contexts: torch.Tensor,
        warmup_bytes: int,
        hidden: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        states, hidden = self.recurrent(self.embedding(previous_bytes), hidden)
        states = states[:, warmup_bytes:, :]
        heads = self.context_head(contexts)
        correction = (heads * states.unsqueeze(2)).sum(dim=-1) / math.sqrt(self.cells)
        correction = correction + self.context_bias(contexts).squeeze(-1)
        return base_logits + correction, hidden


class RangeCounter:
    def __init__(self) -> None:
        self.low = 0
        self.high = 0xFFFFFFFF
        self.bytes = 0

    def encode(self, bit: int, p1: int) -> None:
        delta = self.high - self.low
        midpoint = self.low + (delta >> 16) * p1 + ((delta & 0xFFFF) * p1 >> 16)
        if bit:
            self.high = midpoint
        else:
            self.low = midpoint + 1
        while ((self.low ^ self.high) & 0xFF000000) == 0:
            self.bytes += 1
            self.low = (self.low << 8) & 0xFFFFFFFF
            self.high = ((self.high << 8) + 255) & 0xFFFFFFFF

    def finish(self) -> int:
        while ((self.low ^ self.high) & 0xFF000000) == 0:
            self.bytes += 1
            self.low = (self.low << 8) & 0xFFFFFFFF
            self.high = ((self.high << 8) + 255) & 0xFFFFFFFF
        return self.bytes + 1


def exact_payload(probabilities: np.ndarray, values: np.ndarray) -> int:
    counter = RangeCounter()
    truth = np.unpackbits(values, bitorder="big")
    for bit, p1 in zip(truth, probabilities.reshape(-1), strict=True):
        counter.encode(int(bit), int(p1))
    return counter.finish()


def qbits(probabilities: np.ndarray, values: np.ndarray) -> float:
    truth = np.unpackbits(values, bitorder="big").reshape(-1, 8)
    p = probabilities.astype(np.float64) / 65536.0
    return float(np.where(truth, -np.log2(p), -np.log2(1.0 - p)).sum() * 256.0)


def evaluate_model(
    model: SparseGruDistiller,
    values: np.ndarray,
    base_logits: np.ndarray,
    contexts: np.ndarray,
    chunk_bytes: int,
) -> np.ndarray:
    model.eval()
    outputs: list[np.ndarray] = []
    hidden = None
    previous_value = 0
    with torch.no_grad():
        for lo in range(0, len(values), chunk_bytes):
            hi = min(len(values), lo + chunk_bytes)
            previous = np.empty(hi - lo, dtype=np.int64)
            previous[0] = previous_value
            previous[1:] = values[lo : hi - 1]
            logits, hidden = model(
                torch.from_numpy(previous).unsqueeze(0),
                torch.from_numpy(base_logits[lo:hi]).unsqueeze(0),
                torch.from_numpy(contexts[lo:hi]).unsqueeze(0),
                0,
                hidden,
            )
            probability = torch.sigmoid(logits).mul(65536).round().clamp(1, 65535)
            outputs.append(probability.squeeze(0).to(torch.int32).numpy().astype("<u2"))
            hidden = hidden.detach()
            previous_value = int(values[hi - 1])
    return np.concatenate(outputs, axis=0)


def split_metrics(
    name: str,
    lo: int,
    hi: int,
    source_scope_bytes: int,
    values: np.ndarray,
    base: np.ndarray,
    teacher: np.ndarray,
    candidate: np.ndarray,
) -> dict[str, Any]:
    raw_equivalent = source_scope_bytes * (hi - lo) / len(values)
    base_qbits = qbits(base[lo:hi], values[lo:hi])
    teacher_qbits = qbits(teacher[lo:hi], values[lo:hi])
    candidate_qbits = qbits(candidate[lo:hi], values[lo:hi])
    gain = (base_qbits - candidate_qbits) / 2048.0
    return {
        "split": name,
        "wrt_bytes": hi - lo,
        "source_equivalent_bytes": raw_equivalent,
        "base_qbits": base_qbits,
        "teacher_qbits": teacher_qbits,
        "candidate_qbits": candidate_qbits,
        "teacher_headroom_bytes": (base_qbits - teacher_qbits) / 2048.0,
        "candidate_gain_bytes": gain,
        "candidate_gain_bytes_per_million": gain / raw_equivalent * 1_000_000.0,
        "teacher_headroom_retained_fraction": (
            (base_qbits - candidate_qbits) / (base_qbits - teacher_qbits)
            if base_qbits != teacher_qbits
            else 0.0
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair-trace", type=Path, required=True)
    parser.add_argument("--wrt-store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-scope-bytes", type=int, required=True)
    parser.add_argument("--cells", type=int, default=16)
    parser.add_argument("--embedding-dims", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--sequence-bytes", type=int, default=256)
    parser.add_argument("--warmup-bytes", type=int, default=64)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=0.003)
    parser.add_argument(
        "--objective",
        choices=("teacher_kl", "teacher_residual_logit"),
        default="teacher_kl",
    )
    parser.add_argument("--seed", type=int, default=20260719)
    args = parser.parse_args()

    print(f"python={Path(torch.__file__).resolve()} torch={torch.__version__}")
    print(f"torch.cuda.is_available()={torch.cuda.is_available()}")
    print(f"torch.cuda.device_count()={torch.cuda.device_count()} DEVICE=cpu")
    print(
        "[run-contract] run_name=endpoint_sparse_gru_distill_screen "
        f"pairs_input_spec={args.pair_trace} resume_from=none resume_stage=none "
        "decode=greedy eval_dataset_paths=contiguous_dev,sealed_contiguous_holdout "
        f"device=cpu schedule={args.objective} runtime_mode=cpu sweep_mode=live"
    )
    if args.source_scope_bytes <= 0:
        raise ValueError("source scope must be positive")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(4)

    pair, values = load_inputs(args.pair_trace, args.wrt_store)
    teacher = pair[:, :, 0]
    base = pair[:, :, 1]
    base_logits_np = np.log(base.astype(np.float32) / (65536.0 - base.astype(np.float32)))
    teacher_probabilities = teacher.astype(np.float32) / 65536.0
    contexts = prefix_contexts(values)
    train_end = len(values) * 3 // 5
    holdout_start = len(values) * 4 // 5
    dataset = ChunkDataset(
        values,
        base_logits_np,
        teacher_probabilities,
        contexts,
        train_end,
        args.sequence_bytes,
        args.warmup_bytes,
    )
    generator = torch.Generator().manual_seed(args.seed)
    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        generator=generator,
        num_workers=0,
    )
    model = SparseGruDistiller(args.cells, args.embedding_dims)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=1e-5)
    history = []
    best_development_loss = float("inf")
    best_state: dict[str, torch.Tensor] | None = None
    best_epoch = 0
    for epoch in range(args.epochs):
        model.train()
        total_loss = 0.0
        total_bits = 0
        for previous, base_logits, targets, chunk_contexts in loader:
            optimizer.zero_grad(set_to_none=True)
            logits, _ = model(
                previous,
                base_logits,
                chunk_contexts,
                args.warmup_bytes,
            )
            if args.objective == "teacher_kl":
                loss = nn.functional.binary_cross_entropy_with_logits(logits, targets)
            else:
                teacher_logits = torch.logit(targets.clamp(1.0 / 65536, 65535.0 / 65536))
                loss = nn.functional.smooth_l1_loss(
                    logits - base_logits,
                    teacher_logits - base_logits,
                    beta=0.25,
                )
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            bits = targets.numel()
            total_loss += float(loss.detach()) * bits
            total_bits += bits
        candidate = evaluate_model(
            model,
            values[:holdout_start],
            base_logits_np[:holdout_start],
            contexts[:holdout_start],
            8192,
        )
        development = split_metrics(
            "development",
            train_end,
            holdout_start,
            args.source_scope_bytes,
            values,
            base,
            teacher,
            candidate,
        )
        development_loss = development["candidate_qbits"]
        history.append(
            {
                "epoch": epoch + 1,
                "training_objective_loss": total_loss / total_bits,
                "development_gain_bytes": development["candidate_gain_bytes"],
                "development_gain_bytes_per_million": development[
                    "candidate_gain_bytes_per_million"
                ],
            }
        )
        print(json.dumps(history[-1], sort_keys=True), flush=True)
        if development_loss < best_development_loss:
            best_development_loss = development_loss
            best_epoch = epoch + 1
            best_state = {key: value.detach().clone() for key, value in model.state_dict().items()}
    if best_state is None:
        raise RuntimeError("training produced no checkpoint")
    model.load_state_dict(best_state)
    candidate = evaluate_model(model, values, base_logits_np, contexts, 8192)
    parameter_count = sum(parameter.numel() for parameter in model.parameters())
    tensor_count = len(list(model.parameters()))
    int8_payload_estimate = parameter_count + tensor_count * 8
    required_gain_per_million = (
        TARGET_DEBT_BYTES + int8_payload_estimate
    ) / 1000.0
    splits = [
        split_metrics("train", 0, train_end, args.source_scope_bytes, values, base, teacher, candidate),
        split_metrics("development", train_end, holdout_start, args.source_scope_bytes, values, base, teacher, candidate),
        split_metrics("holdout", holdout_start, len(values), args.source_scope_bytes, values, base, teacher, candidate),
        split_metrics("all", 0, len(values), args.source_scope_bytes, values, base, teacher, candidate),
    ]
    baseline_payload = exact_payload(base, values)
    candidate_payload = exact_payload(candidate, values)
    teacher_payload = exact_payload(teacher, values)
    holdout = splits[2]
    all_split = splits[3]
    quantization_gate = (
        holdout["candidate_gain_bytes_per_million"] >= required_gain_per_million
        and baseline_payload - candidate_payload >= required_gain_per_million
    )
    receipt = {
        "schema": "endpoint_sparse_gru_distill_screen_v1",
        "evidence_level": "offline_teacher_causal_float_shadow",
        "hypothesis": (
            "A learned cross-state byte recurrence can retain enough of the compact endpoint's "
            "same-execution complement over fast FX2 to justify fixed-point quantization."
        ),
        "inputs": {
            "pair_trace": str(args.pair_trace.resolve()),
            "pair_trace_sha256": sha256(args.pair_trace),
            "wrt_store": str(args.wrt_store.resolve()),
            "wrt_store_sha256": sha256(args.wrt_store),
            "teacher_pair_endpoint": 0,
            "base_pair_endpoint": 1,
            "source_scope_bytes": args.source_scope_bytes,
            "wrt_bytes": len(values),
        },
        "implementation": {
            "source": str(Path(__file__).resolve()),
            "source_sha256": sha256(Path(__file__)),
            "torch_version": torch.__version__,
            "device": "cpu",
        },
        "selection": {
            "seed": args.seed,
            "objective": args.objective,
            "train_fraction": 0.6,
            "development_fraction": 0.2,
            "holdout_fraction": 0.2,
            "holdout_reads_during_selection": False,
            "selected_epoch": best_epoch,
            "history": history,
        },
        "model": {
            "cells": args.cells,
            "embedding_dims": args.embedding_dims,
            "parameter_count": parameter_count,
            "float_parameter_bytes": parameter_count * 4,
            "estimated_int8_payload_bytes": int8_payload_estimate,
            "sequence_bytes": args.sequence_bytes,
            "warmup_bytes": args.warmup_bytes,
        },
        "economics": {
            "target_debt_bytes": TARGET_DEBT_BYTES,
            "required_gain_before_payload_bytes_per_million": TARGET_DEBT_BYTES / 1000.0,
            "required_gain_with_estimated_int8_payload_bytes_per_million": required_gain_per_million,
        },
        "splits": splits,
        "exact_full_scope_replay": {
            "baseline_payload_bytes": baseline_payload,
            "teacher_payload_bytes": teacher_payload,
            "candidate_payload_bytes": candidate_payload,
            "candidate_saved_bytes": baseline_payload - candidate_payload,
        },
        "quantization_gate_passed": quantization_gate,
        "promotion_authorized": False,
        "decision": (
            "quantize one frozen model and replay fixed-point causally"
            if quantization_gate
            else "retire this learned recurrent representation before native integration"
        ),
        "claim_boundary": (
            "Offline float teacher distillation with causal replay. The compact teacher is not "
            "decoder-available; weights are not yet quantized or counted; no archive, native "
            "runtime, memory, disjoint transfer, or full-corpus claim is established."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(args.output), "quantization_gate_passed": quantization_gate}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
