#!/usr/bin/env python3
"""Bounded ROCm oracle for a frozen causal endpoint428 residual model."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import struct
import sys
import zlib


ROCM_PYTHON = Path(
    "/home/x/enwiki9-nonproof/external/rocm-pytorch-venv/bin/python"
)
DEFAULT_P1 = Path(
    "/home/x/enwiki9-nonproof/results/"
    "endpoint428_pair_layer0_online_native_1m_v1/native.p1"
)
DEFAULT_WRT = Path(
    "/home/x/enwiki9-nonproof/results/fx2_wrt_store_1m.bin"
)
DEFAULT_RESULTS = Path(
    "results/chiron_frozen_residual_lm_opening_1m_v1"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p1", type=Path, default=DEFAULT_P1)
    parser.add_argument("--wrt", type=Path, default=DEFAULT_WRT)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--raw-bytes", type=int, default=1_000_000)
    parser.add_argument("--expected-parent-payload", type=int, default=173_859)
    parser.add_argument("--block-size", type=int, default=256)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--seed", type=int, default=428)
    return parser.parse_args()


def ensure_rocm() -> None:
    if os.environ.get("CHIRON_ROCM_REEXEC") == "1":
        return
    if not ROCM_PYTHON.is_file():
        raise SystemExit(f"missing receipt-bound ROCm interpreter: {ROCM_PYTHON}")
    env = os.environ.copy()
    env["CHIRON_ROCM_REEXEC"] = "1"
    env["AMD_SERIALIZE_KERNEL"] = "3"
    os.execve(
        str(ROCM_PYTHON),
        [str(ROCM_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
        env,
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_p1(path: Path, expected_rows: int):
    import numpy as np

    raw = path.read_bytes()
    if len(raw) < 16:
        raise ValueError("p1 trace is shorter than its 16-byte header")
    declared_rows = struct.unpack("<Q", raw[8:16])[0]
    values = np.frombuffer(raw, dtype="<u2", offset=16).copy()
    if declared_rows != len(values):
        raise ValueError(
            f"p1 row declaration mismatch: {declared_rows} != {len(values)}"
        )
    if len(values) != expected_rows:
        raise ValueError(
            f"p1/WRT row mismatch: {len(values)} != {expected_rows}"
        )
    return raw[:8].hex(), values


def range_coded_size(probabilities, truth_bits) -> int:
    x1 = 0
    x2 = 0xFFFFFFFF
    emitted = 0
    for probability, truth in zip(probabilities, truth_bits):
        p1 = int(probability)
        delta = x2 - x1
        midpoint = x1 + (delta >> 16) * p1 + ((delta & 0xFFFF) * p1 >> 16)
        if int(truth):
            x2 = midpoint
        else:
            x1 = midpoint + 1
        while ((x1 ^ x2) & 0xFF000000) == 0:
            emitted += 1
            x1 = (x1 << 8) & 0xFFFFFFFF
            x2 = ((x2 << 8) & 0xFFFFFFFF) + 255
    while ((x1 ^ x2) & 0xFF000000) == 0:
        emitted += 1
        x1 = (x1 << 8) & 0xFFFFFFFF
        x2 = ((x2 << 8) & 0xFFFFFFFF) + 255
    return emitted + 1


def probability_logits(probabilities):
    import numpy as np

    p = np.clip(probabilities.astype(np.float64), 1, 65535) / 65536.0
    return np.log(p) - np.log1p(-p)


def quantized_probabilities(base_logits, residuals):
    import numpy as np

    logits = np.clip(base_logits + residuals, -20.0, 20.0)
    values = 65536.0 / (1.0 + np.exp(-logits))
    return np.clip(np.rint(values), 1, 65535).astype(np.uint16)


def fit_node_bias(train_logits, train_nodes, train_bits):
    import numpy as np

    logits = train_logits.reshape(-1).astype(np.float64)
    nodes = train_nodes.reshape(-1).astype(np.int64)
    truth = train_bits.reshape(-1).astype(np.float64)
    residual = np.zeros(255, dtype=np.float64)
    for _ in range(12):
        adjusted = np.clip(logits + residual[nodes], -20.0, 20.0)
        prediction = 1.0 / (1.0 + np.exp(-adjusted))
        gradient = np.bincount(
            nodes, weights=prediction - truth, minlength=255
        )
        curvature = np.bincount(
            nodes,
            weights=prediction * (1.0 - prediction),
            minlength=255,
        )
        step = gradient / np.maximum(curvature, 1e-9)
        residual -= np.clip(step, -2.0, 2.0)
        if float(np.max(np.abs(step))) < 1e-7:
            break
    return residual.astype(np.float32)


def main() -> int:
    args = parse_args()
    ensure_rocm()

    import numpy as np
    import torch
    from torch import nn

    if not torch.cuda.is_available():
        raise SystemExit("receipt-bound ROCm PyTorch has no visible GPU")

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

    device = torch.device("cuda")
    args.results.mkdir(parents=True, exist_ok=True)

    wrt_raw = args.wrt.read_bytes()
    if len(wrt_raw) <= 5:
        raise ValueError("WRT store is missing its five-byte header")
    wrt = np.frombuffer(wrt_raw, dtype=np.uint8, offset=5).copy()
    p1_magic, p1 = read_p1(args.p1, len(wrt) * 8)
    truth_bits_all = np.unpackbits(wrt, bitorder="big")

    parent_payload = range_coded_size(p1, truth_bits_all)
    if parent_payload != args.expected_parent_payload:
        raise ValueError(
            "exact parent replay failed: "
            f"{parent_payload} != {args.expected_parent_payload}"
        )

    block_size = args.block_size
    complete_bytes = (len(wrt) // block_size) * block_size
    block_count = complete_bytes // block_size
    if block_count < 20:
        raise ValueError("population has too few complete causal blocks")

    wrt_blocks = wrt[:complete_bytes].reshape(block_count, block_size)
    p1_blocks = p1[: complete_bytes * 8].reshape(
        block_count, block_size, 8
    )
    bits = np.unpackbits(wrt_blocks[..., None], axis=2, bitorder="big")

    nodes = np.empty((block_count, block_size, 8), dtype=np.uint16)
    for bit_position in range(8):
        if bit_position == 0:
            prefix = np.zeros_like(wrt_blocks, dtype=np.uint16)
        else:
            prefix = (
                wrt_blocks.astype(np.uint16) >> (8 - bit_position)
            )
        nodes[:, :, bit_position] = (
            (1 << bit_position) - 1 + prefix
        )

    inputs = np.empty((block_count, block_size), dtype=np.int64)
    inputs[:, 0] = 256
    inputs[:, 1:] = wrt_blocks[:, :-1]
    base_logits = probability_logits(p1_blocks).astype(np.float32)

    train_count = int(block_count * 0.70)
    dev_count = int(block_count * 0.15)
    dev_start = train_count
    hold_start = train_count + dev_count
    if min(train_count, dev_count, block_count - hold_start) <= 0:
        raise ValueError("chronological split produced an empty population")

    class Chiron(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.embedding = nn.Embedding(257, 64)
            self.gru = nn.GRU(
                input_size=64,
                hidden_size=96,
                num_layers=2,
                batch_first=True,
            )
            self.readout = nn.Linear(96, 255)

        def forward(self, token_input):
            embedded = self.embedding(token_input)
            state, _ = self.gru(embedded)
            return self.readout(state)

    model = Chiron().to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=0.002, weight_decay=1e-6
    )

    def batch_loss(block_indices, train: bool):
        token_input = torch.from_numpy(inputs[block_indices]).to(device)
        batch_nodes = torch.from_numpy(
            nodes[block_indices].astype(np.int64)
        ).to(device)
        baseline = torch.from_numpy(base_logits[block_indices]).to(device)
        truth = torch.from_numpy(
            bits[block_indices].astype(np.float32)
        ).to(device)
        outputs = model(token_input)
        selected = torch.gather(outputs, 2, batch_nodes)
        loss = nn.functional.binary_cross_entropy_with_logits(
            baseline + selected, truth
        )
        if train:
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
        return float(loss.detach().cpu())

    def population_loss(start: int, stop: int) -> float:
        model.eval()
        weighted = 0.0
        examples = 0
        with torch.no_grad():
            for batch_start in range(start, stop, args.batch_size):
                batch_stop = min(batch_start + args.batch_size, stop)
                indices = np.arange(batch_start, batch_stop)
                value = batch_loss(indices, False)
                count = len(indices)
                weighted += value * count
                examples += count
        return weighted / examples

    best_dev = math.inf
    best_state = None
    epoch_receipts = []
    rng = np.random.default_rng(args.seed)
    for epoch in range(args.epochs):
        model.train()
        ordering = rng.permutation(train_count)
        total_loss = 0.0
        batch_total = 0
        for offset in range(0, train_count, args.batch_size):
            index = ordering[offset : offset + args.batch_size]
            total_loss += batch_loss(index, True)
            batch_total += 1
        dev_loss = population_loss(dev_start, hold_start)
        train_loss = total_loss / batch_total
        epoch_receipts.append(
            {
                "epoch": epoch + 1,
                "train_nats_per_bit": train_loss,
                "development_nats_per_bit": dev_loss,
            }
        )
        print(
            f"epoch={epoch + 1} train={train_loss:.8f} "
            f"development={dev_loss:.8f}",
            flush=True,
        )
        if dev_loss < best_dev:
            best_dev = dev_loss
            best_state = {
                name: tensor.detach().cpu().clone()
                for name, tensor in model.state_dict().items()
            }

    if best_state is None:
        raise RuntimeError("training did not produce a model state")
    model.load_state_dict(best_state)

    quantized_tensors = {}
    quantized_state = {}
    for name, tensor in best_state.items():
        array = tensor.numpy().astype(np.float32)
        maximum = float(np.max(np.abs(array)))
        scale = maximum / 127.0 if maximum > 0.0 else 1.0
        quantized = np.clip(np.rint(array / scale), -127, 127).astype(
            np.int8
        )
        quantized_tensors[f"{name}.q"] = quantized
        quantized_tensors[f"{name}.scale"] = np.array(
            [scale], dtype=np.float32
        )
        quantized_state[name] = torch.from_numpy(
            quantized.astype(np.float32) * scale
        )
    model.load_state_dict(quantized_state)
    model.to(device)
    model.eval()

    model_path = args.results / "chiron_q0_int8_tensors.npz"
    np.savez_compressed(model_path, **quantized_tensors)
    model_package_bytes = model_path.stat().st_size
    source_package_bytes = len(
        zlib.compress(Path(__file__).read_bytes(), level=9)
    )
    provisional_package_bytes = model_package_bytes + source_package_bytes

    def infer_selected_residuals(start: int, stop: int):
        result = np.empty((stop - start, block_size, 8), dtype=np.float32)
        cursor = 0
        with torch.no_grad():
            for batch_start in range(start, stop, args.batch_size):
                batch_stop = min(batch_start + args.batch_size, stop)
                index = np.arange(batch_start, batch_stop)
                token_input = torch.from_numpy(inputs[index]).to(device)
                batch_nodes = torch.from_numpy(
                    nodes[index].astype(np.int64)
                ).to(device)
                outputs = model(token_input)
                selected = torch.gather(outputs, 2, batch_nodes)
                host = selected.cpu().numpy().astype(np.float32)
                result[cursor : cursor + len(index)] = host
                cursor += len(index)
        return result

    node_bias = fit_node_bias(
        base_logits[:train_count],
        nodes[:train_count],
        bits[:train_count],
    )

    dev_residual = infer_selected_residuals(dev_start, hold_start)
    hold_residual = infer_selected_residuals(hold_start, block_count)

    def exact_population(start: int, stop: int, residual):
        local_p1 = p1_blocks[start:stop].reshape(-1)
        local_bits = bits[start:stop].reshape(-1)
        baseline_bytes = range_coded_size(local_p1, local_bits)
        local_logits = base_logits[start:stop]
        adjusted = quantized_probabilities(local_logits, residual).reshape(-1)
        candidate_bytes = range_coded_size(adjusted, local_bits)
        return baseline_bytes, candidate_bytes

    dev_base, dev_candidate = exact_population(
        dev_start, hold_start, dev_residual
    )
    hold_base, hold_candidate = exact_population(
        hold_start, block_count, hold_residual
    )
    hold_bias = node_bias[nodes[hold_start:block_count]]
    _, hold_bias_candidate = exact_population(
        hold_start, block_count, hold_bias
    )
    shifted = np.roll(
        hold_residual.reshape(-1, 8), shift=4093, axis=0
    ).reshape(hold_residual.shape)
    _, hold_shift_candidate = exact_population(
        hold_start, block_count, shifted
    )

    dev_gain = dev_base - dev_candidate
    hold_gain = hold_base - hold_candidate
    bias_gain = hold_base - hold_bias_candidate
    shift_gain = hold_base - hold_shift_candidate
    hold_wrt_bytes = (block_count - hold_start) * block_size
    hold_raw_bytes = (
        args.raw_bytes * hold_wrt_bytes / float(len(wrt))
    )
    gross_bpm = hold_gain * 1_000_000.0 / hold_raw_bytes
    package_bpm = provisional_package_bytes / 1000.0
    net_bpm = gross_bpm - package_bpm

    authorized = (
        dev_gain > 0
        and gross_bpm >= 3000.0
        and net_bpm >= 2100.0
        and hold_gain > bias_gain
        and hold_gain > shift_gain
    )
    verdict = "AUTHORIZED_Q1" if authorized else "REJECT"

    decision = {
        "schema": "gamma.chiron_frozen_residual_oracle.v1",
        "candidate": "chiron_frozen_residual_lm_q0_v1",
        "verdict": verdict,
        "score_credit_bytes": 0,
        "reason": (
            "All predeclared target-scale and control gates passed."
            if authorized
            else "At least one predeclared target-scale or control gate failed."
        ),
        "inputs": {
            "p1_path": str(args.p1),
            "p1_sha256": sha256_file(args.p1),
            "p1_magic_hex": p1_magic,
            "wrt_path": str(args.wrt),
            "wrt_sha256": sha256_file(args.wrt),
            "raw_bytes": args.raw_bytes,
            "wrt_bytes": len(wrt),
            "complete_wrt_bytes": complete_bytes,
            "parent_payload_expected": args.expected_parent_payload,
            "parent_payload_replayed": parent_payload,
        },
        "architecture": {
            "block_size": block_size,
            "embedding_width": 64,
            "hidden_width": 96,
            "gru_layers": 2,
            "readout_nodes": 255,
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "seed": args.seed,
            "parameter_count": sum(
                parameter.numel() for parameter in model.parameters()
            ),
            "quantization": "symmetric signed int8 per tensor, dequantized oracle",
        },
        "split": {
            "blocks": block_count,
            "train_blocks": train_count,
            "development_blocks": dev_count,
            "holdout_blocks": block_count - hold_start,
            "ignored_tail_wrt_bytes": len(wrt) - complete_bytes,
            "estimated_holdout_raw_bytes": hold_raw_bytes,
        },
        "exact_bytes": {
            "development_baseline": dev_base,
            "development_chiron": dev_candidate,
            "development_gain": dev_gain,
            "holdout_baseline": hold_base,
            "holdout_chiron": hold_candidate,
            "holdout_gain": hold_gain,
            "holdout_node_bias": hold_bias_candidate,
            "holdout_node_bias_gain": bias_gain,
            "holdout_shifted": hold_shift_candidate,
            "holdout_shifted_gain": shift_gain,
        },
        "economics": {
            "gross_holdout_bytes_per_million_raw": gross_bpm,
            "model_npz_bytes": model_package_bytes,
            "compressed_oracle_source_bytes": source_package_bytes,
            "provisional_package_bytes": provisional_package_bytes,
            "package_amortized_bytes_per_million": package_bpm,
            "net_holdout_bytes_per_million_raw": net_bpm,
        },
        "gates": {
            "exact_parent_trace_replay": parent_payload
            == args.expected_parent_payload,
            "development_gain_positive": dev_gain > 0,
            "gross_at_least_3000_bpm": gross_bpm >= 3000.0,
            "net_at_least_2100_bpm": net_bpm >= 2100.0,
            "beats_node_bias": hold_gain > bias_gain,
            "beats_shift_null": hold_gain > shift_gain,
        },
        "training": epoch_receipts,
        "limitations": [
            "The int8 tensors are dequantized for this oracle.",
            "No deterministic integer GRU decoder exists yet.",
            "The package charge is provisional and not a counted submission package.",
            "Opening-1M chronological holdout is not distant transfer.",
            "This receipt has zero forecast and score credit.",
        ],
    }
    decision_path = args.results / "decision.json"
    decision_path.write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision["exact_bytes"], sort_keys=True), flush=True)
    print(json.dumps(decision["economics"], sort_keys=True), flush=True)
    print(f"verdict={verdict}", flush=True)
    return 0 if authorized else 2


if __name__ == "__main__":
    raise SystemExit(main())
