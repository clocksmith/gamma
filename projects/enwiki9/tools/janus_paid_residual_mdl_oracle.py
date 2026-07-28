#!/usr/bin/env python3
"""Paid fixed-population MDL oracle over exact endpoint428 residuals."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random
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


def ensure_rocm() -> None:
    if os.environ.get("JANUS_ROCM_REEXEC") == "1":
        return
    environment = os.environ.copy()
    environment["JANUS_ROCM_REEXEC"] = "1"
    environment["AMD_SERIALIZE_KERNEL"] = "3"
    os.execve(
        str(ROCM_PYTHON),
        [str(ROCM_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
        environment,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p1", type=Path, default=DEFAULT_P1)
    parser.add_argument("--wrt", type=Path, default=DEFAULT_WRT)
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("results/janus_paid_residual_mdl_1m_v1"),
    )
    parser.add_argument("--raw-bytes", type=int, default=1_000_000)
    parser.add_argument("--expected-parent-payload", type=int, default=173859)
    args = parser.parse_args()
    ensure_rocm()

    import numpy as np
    import torch
    from torch import nn

    tools_dir = Path(__file__).resolve().parent
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    import chiron_residual_oracle as chiron

    seed = 428
    block_size = 256
    batch_size = 32
    epochs = 8
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    if not torch.cuda.is_available():
        raise SystemExit("receipt-bound ROCm PyTorch has no visible GPU")
    device = torch.device("cuda")
    args.results.mkdir(parents=True, exist_ok=True)

    wrt_raw = args.wrt.read_bytes()
    wrt = np.frombuffer(wrt_raw, dtype=np.uint8, offset=5).copy()
    p1_magic, p1 = chiron.read_p1(args.p1, len(wrt) * 8)
    all_truth = np.unpackbits(wrt, bitorder="big")
    parent_payload = chiron.range_coded_size(p1, all_truth)
    if parent_payload != args.expected_parent_payload:
        raise ValueError(
            f"parent replay failed: {parent_payload} != "
            f"{args.expected_parent_payload}"
        )

    complete_bytes = (len(wrt) // block_size) * block_size
    block_count = complete_bytes // block_size
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
    base_logits = chiron.probability_logits(p1_blocks).astype(np.float32)

    class Janus(nn.Module):
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

    model = Janus().to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=0.002, weight_decay=1e-6
    )
    rng = np.random.default_rng(seed)
    epoch_receipts = []

    def train_batch(indices):
        token_input = torch.from_numpy(inputs[indices]).to(device)
        batch_nodes = torch.from_numpy(
            nodes[indices].astype(np.int64)
        ).to(device)
        baseline = torch.from_numpy(base_logits[indices]).to(device)
        truth = torch.from_numpy(
            bits[indices].astype(np.float32)
        ).to(device)
        output = model(token_input)
        selected = torch.gather(output, 2, batch_nodes)
        loss = nn.functional.binary_cross_entropy_with_logits(
            baseline + selected, truth
        )
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        return float(loss.detach().cpu())

    for epoch in range(epochs):
        model.train()
        ordering = rng.permutation(block_count)
        total = 0.0
        batches = 0
        for offset in range(0, block_count, batch_size):
            indices = ordering[offset : offset + batch_size]
            total += train_batch(indices)
            batches += 1
        mean_loss = total / batches
        epoch_receipts.append(
            {"epoch": epoch + 1, "training_nats_per_bit": mean_loss}
        )
        print(
            f"epoch={epoch + 1} training={mean_loss:.8f}",
            flush=True,
        )

    quantized = {}
    dequantized_state = {}
    for name, tensor in model.state_dict().items():
        array = tensor.detach().cpu().numpy().astype(np.float32)
        maximum = float(np.max(np.abs(array)))
        scale = maximum / 127.0 if maximum > 0.0 else 1.0
        values = np.clip(
            np.rint(array / scale), -127, 127
        ).astype(np.int8)
        quantized[f"{name}.q"] = values
        quantized[f"{name}.scale"] = np.array(
            [scale], dtype=np.float32
        )
        dequantized_state[name] = torch.from_numpy(
            values.astype(np.float32) * scale
        )
    model.load_state_dict(dequantized_state)
    model.to(device)
    model.eval()

    model_path = args.results / "janus_q0_int8_tensors.npz"
    np.savez_compressed(model_path, **quantized)
    model_bytes = model_path.stat().st_size
    source_bytes = len(
        zlib.compress(Path(__file__).read_bytes(), level=9)
    )
    package_bytes = model_bytes + source_bytes

    selected_residuals = np.empty(
        (block_count, block_size, 8), dtype=np.float32
    )
    with torch.no_grad():
        for offset in range(0, block_count, batch_size):
            stop = min(offset + batch_size, block_count)
            indices = np.arange(offset, stop)
            token_input = torch.from_numpy(inputs[indices]).to(device)
            batch_nodes = torch.from_numpy(
                nodes[indices].astype(np.int64)
            ).to(device)
            output = model(token_input)
            selected = torch.gather(output, 2, batch_nodes)
            selected_residuals[offset:stop] = (
                selected.cpu().numpy().astype(np.float32)
            )

    flat_p1 = p1_blocks.reshape(-1)
    flat_bits = bits.reshape(-1)
    baseline_bytes = chiron.range_coded_size(flat_p1, flat_bits)
    candidate_p1 = chiron.quantized_probabilities(
        base_logits, selected_residuals
    ).reshape(-1)
    candidate_bytes = chiron.range_coded_size(candidate_p1, flat_bits)

    node_bias = chiron.fit_node_bias(base_logits, nodes, bits)
    bias_p1 = chiron.quantized_probabilities(
        base_logits, node_bias[nodes]
    ).reshape(-1)
    bias_bytes = chiron.range_coded_size(bias_p1, flat_bits)

    shifted_residuals = np.roll(
        selected_residuals.reshape(-1, 8), shift=4093, axis=0
    ).reshape(selected_residuals.shape)
    shifted_p1 = chiron.quantized_probabilities(
        base_logits, shifted_residuals
    ).reshape(-1)
    shifted_bytes = chiron.range_coded_size(shifted_p1, flat_bits)

    gain = baseline_bytes - candidate_bytes
    bias_gain = baseline_bytes - bias_bytes
    shifted_gain = baseline_bytes - shifted_bytes
    represented_raw = (
        args.raw_bytes * complete_bytes / float(len(wrt))
    )
    gross_bpm = gain * 1_000_000.0 / represented_raw
    package_bpm = package_bytes / 1000.0
    projected_net_bpm = gross_bpm - package_bpm
    projected_full_corpus_net_bytes = (
        gross_bpm * 1000.0 - package_bytes
    )
    literal_population_delta = package_bytes - gain
    authorized = (
        gross_bpm >= 3000.0
        and projected_net_bpm >= 2100.0
        and gain > bias_gain
        and gain > shifted_gain
    )
    decision = {
        "schema": "gamma.janus_paid_residual_mdl_oracle.v1",
        "candidate": "janus_paid_residual_mdl_q0_v1",
        "verdict": "AUTHORIZED_10M" if authorized else "REJECT",
        "score_credit_bytes": 0,
        "inputs": {
            "p1_path": str(args.p1),
            "p1_magic_hex": p1_magic,
            "wrt_path": str(args.wrt),
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
            "epochs": epochs,
            "parameter_count": sum(
                parameter.numel() for parameter in model.parameters()
            ),
            "selection": "fixed final epoch",
            "quantization": (
                "symmetric signed int8 per tensor, dequantized oracle"
            ),
        },
        "exact_bytes": {
            "baseline": baseline_bytes,
            "janus": candidate_bytes,
            "janus_gain": gain,
            "node_bias": bias_bytes,
            "node_bias_gain": bias_gain,
            "shifted": shifted_bytes,
            "shifted_gain": shifted_gain,
        },
        "economics": {
            "represented_raw_bytes": represented_raw,
            "gross_bytes_per_million": gross_bpm,
            "model_npz_bytes": model_bytes,
            "compressed_source_bytes": source_bytes,
            "provisional_package_bytes": package_bytes,
            "package_amortized_bytes_per_million": package_bpm,
            "projected_net_bytes_per_million": projected_net_bpm,
            "projected_full_corpus_net_savings_bytes": (
                projected_full_corpus_net_bytes
            ),
            "literal_population_two_part_delta_bytes": (
                literal_population_delta
            ),
        },
        "gates": {
            "parent_trace_exact": parent_payload
            == args.expected_parent_payload,
            "gross_at_least_3000_bpm": gross_bpm >= 3000.0,
            "projected_net_at_least_2100_bpm": (
                projected_net_bpm >= 2100.0
            ),
            "beats_node_bias": gain > bias_gain,
            "beats_shift_null": gain > shifted_gain,
        },
        "training": epoch_receipts,
        "limitations": [
            "Training and evaluation use the same fixed population.",
            "The int8 tensors are dequantized for oracle execution.",
            "No deterministic integer decoder exists.",
            "The 1G economics are an amortization screen, not transfer proof.",
            "The model adds runtime and does not replace Gamma substrate.",
            "This receipt has zero forecast and score credit.",
        ],
    }
    (args.results / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision["exact_bytes"], sort_keys=True))
    print(json.dumps(decision["economics"], sort_keys=True))
    print(f"verdict={decision['verdict']}")
    return 0 if authorized else 2


if __name__ == "__main__":
    raise SystemExit(main())
