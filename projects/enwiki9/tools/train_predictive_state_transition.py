#!/usr/bin/env python3
"""Train a compact causal transition model for a finite recurrent-state quotient."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np
import torch
from torch import nn

from screen_predictive_state_quotient import assign, train_kmeans


MAGIC = b"DPLRST2\0"
HEADER = struct.Struct("<8s5I")


class TransitionModel(nn.Module):
    def __init__(self, states: int, features: int, event_classes: int, rank: int):
        super().__init__()
        self.state = nn.Embedding(states, rank)
        self.event = nn.Embedding(event_classes, rank)
        self.features = nn.Linear(features, rank, bias=False)
        self.output = nn.Linear(rank, states)

    def forward(
        self, state: torch.Tensor, features: torch.Tensor, event: torch.Tensor
    ) -> torch.Tensor:
        hidden = torch.tanh(
            self.state(state) + self.event(event) + self.features(features)
        )
        return self.output(hidden)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate(
    model: TransitionModel,
    codes: np.ndarray,
    features: np.ndarray,
    events: np.ndarray,
    start: int,
    end: int,
) -> dict[str, object]:
    with torch.no_grad():
        source = torch.from_numpy(codes[start : end - 1].astype(np.int64))
        x = torch.from_numpy(features[start + 1 : end])
        event = torch.from_numpy(events[start + 1 : end].astype(np.int64))
        target = codes[start + 1 : end]
        predicted = model(source, x, event).argmax(dim=1).numpy()
        teacher_forced = float(np.mean(predicted == target))

        rolled = int(codes[start])
        hits = 0
        first_divergence = None
        for index in range(start + 1, end):
            prediction = int(
                model(
                    torch.tensor([rolled]),
                    torch.from_numpy(features[index : index + 1]),
                    torch.tensor([int(events[index])]),
                )
                .argmax(dim=1)
                .item()
            )
            rolled = prediction
            expected = int(codes[index])
            if prediction == expected:
                hits += 1
            elif first_divergence is None:
                first_divergence = index - start
    transitions = end - start - 1
    return {
        "transitions": transitions,
        "teacher_forced_accuracy": teacher_forced,
        "continuous_rollout_accuracy": hits / transitions,
        "first_rollout_divergence": first_divergence,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--states", type=int, default=64)
    parser.add_argument("--pca-dims", type=int, default=16)
    parser.add_argument("--transition-rank", type=int, default=16)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--learning-rate", type=float, default=0.002)
    parser.add_argument("--train-fraction", type=float, default=0.7)
    parser.add_argument("--seed", type=int, default=428)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    torch.set_num_threads(args.threads)
    rng = np.random.default_rng(args.seed)
    with args.trace.open("rb") as source:
        header = source.read(HEADER.size)
    magic, version, feature_count, cells, row_bytes, flags = HEADER.unpack(header)
    if magic != MAGIC or version != 2 or cells != 112:
        raise ValueError("unsupported state trace")
    dtype = np.dtype(
        [
            ("event", "<u4"),
            ("x", "<f4", (feature_count,)),
            ("h0", "<f4", (cells,)),
            ("c0", "<f4", (cells,)),
            ("h1", "<f4", (cells,)),
            ("c1", "<f4", (cells,)),
        ]
    )
    if dtype.itemsize != row_bytes:
        raise ValueError("state trace row size mismatch")
    rows = (args.trace.stat().st_size - HEADER.size) // row_bytes
    trace = np.memmap(
        args.trace, mode="r", dtype=dtype, offset=HEADER.size, shape=(rows,)
    )
    state = np.concatenate(
        [trace["h0"], trace["c0"], trace["h1"], trace["c1"]], axis=1
    ).astype(np.float32)
    x = np.asarray(trace["x"], dtype=np.float32)
    events = np.asarray(trace["event"], dtype=np.int64)
    if int(events.max()) >= 256:
        raise ValueError("event class exceeds transition embedding")
    train_end = int(rows * args.train_fraction)
    split = (train_end + rows) // 2

    sample_indices = np.linspace(
        0, train_end - 1, min(20000, train_end), dtype=np.int64
    )
    sample = state[sample_indices].astype(np.float64)
    mean = sample.mean(axis=0)
    covariance = (sample - mean).T @ (sample - mean) / len(sample)
    _, eigenvectors = np.linalg.eigh(covariance)
    basis = eigenvectors[:, -args.pca_dims :]
    projected = ((state - mean) @ basis).astype(np.float32)
    centers = train_kmeans(
        projected[:train_end], args.states, 24, 4096, rng
    )
    codes = assign(projected, centers)

    x_mean = x[:train_end].mean(axis=0)
    x_scale = x[:train_end].std(axis=0)
    x_scale[x_scale < 1e-5] = 1.0
    x = ((x - x_mean) / x_scale).astype(np.float32)

    model = TransitionModel(args.states, feature_count, 256, args.transition_rank)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate)
    train_rows = train_end - 1
    for epoch in range(args.epochs):
        order = rng.permutation(train_rows)
        total_loss = 0.0
        for start in range(0, train_rows, args.batch_size):
            indices = order[start : start + args.batch_size]
            source = torch.from_numpy(codes[indices].astype(np.int64))
            features = torch.from_numpy(x[indices + 1])
            event = torch.from_numpy(events[indices + 1])
            target = torch.from_numpy(codes[indices + 1].astype(np.int64))
            optimizer.zero_grad(set_to_none=True)
            loss = nn.functional.cross_entropy(
                model(source, features, event), target
            )
            loss.backward()
            optimizer.step()
            total_loss += float(loss) * len(indices)
        print(json.dumps({"epoch": epoch + 1, "loss_nats": total_loss / train_rows}))

    parameter_count = sum(parameter.numel() for parameter in model.parameters())
    result = {
        "schema": "predictive_state_transition_v1",
        "trace": {
            "path": str(args.trace.resolve()),
            "bytes": args.trace.stat().st_size,
            "sha256": sha256_file(args.trace),
            "rows": rows,
            "flags": flags,
        },
        "model": {
            "states": args.states,
            "pca_dims_offline_only": args.pca_dims,
            "transition_rank": args.transition_rank,
            "parameter_count": parameter_count,
            "estimated_int8_parameter_bytes": parameter_count,
        },
        "development": evaluate(model, codes, x, events, train_end, split),
        "holdout": evaluate(model, codes, x, events, split, rows),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
