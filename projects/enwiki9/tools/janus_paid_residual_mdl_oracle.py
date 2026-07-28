#!/usr/bin/env python3
"""Exact paid fixed-population MDL witness over endpoint428 residuals."""

from __future__ import annotations

import argparse
import hashlib
import json
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
DEFAULT_RAW = Path(
    "/home/x/enwiki9-nonproof/results/"
    "fx2_full_attribution_trace_1m_v1.restored"
)
DEFAULT_ARCHIVE = Path(
    "/home/x/enwiki9-nonproof/results/"
    "endpoint428_pair_layer0_online_native_1m_v1/archive.bin"
)
DEFAULT_INVERSE_RECEIPT = Path(
    "results/endpoint_final_trace_1m_v1/manifest.json"
)
J1_DECODER_ALLOWANCE = 16_384
J2_DECODER_ALLOWANCE = 65_536
OUTER_FRAME_BYTES = 32
PACKAGE_CEILING = 256_000


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
        raise ValueError("P1 trace is shorter than its 16-byte header")
    declared_rows = struct.unpack("<Q", raw[8:16])[0]
    values = np.frombuffer(raw, dtype="<u2", offset=16).copy()
    if declared_rows != len(values):
        raise ValueError("P1 row declaration mismatch")
    if len(values) != expected_rows:
        raise ValueError(
            f"P1/WRT row mismatch: {len(values)} != {expected_rows}"
        )
    return raw[:8].hex(), values


def range_encode(probabilities, truth_bits) -> bytes:
    output = bytearray()
    x1 = 0
    x2 = 0xFFFFFFFF
    for probability, truth in zip(probabilities, truth_bits):
        p1 = int(probability)
        delta = x2 - x1
        midpoint = x1 + (delta >> 16) * p1 + (
            (delta & 0xFFFF) * p1 >> 16
        )
        if int(truth):
            x2 = midpoint
        else:
            x1 = midpoint + 1
        while ((x1 ^ x2) & 0xFF000000) == 0:
            output.append((x2 >> 24) & 0xFF)
            x1 = (x1 << 8) & 0xFFFFFFFF
            x2 = ((x2 << 8) & 0xFFFFFFFF) + 255
    while ((x1 ^ x2) & 0xFF000000) == 0:
        output.append((x2 >> 24) & 0xFF)
        x1 = (x1 << 8) & 0xFFFFFFFF
        x2 = ((x2 << 8) & 0xFFFFFFFF) + 255
    output.append((x2 >> 24) & 0xFF)
    return bytes(output)


def range_decode(payload: bytes, probabilities):
    import numpy as np

    if len(payload) < 4:
        raise ValueError("range payload is too short")
    cursor = 4
    code = int.from_bytes(payload[:4], "big")
    x1 = 0
    x2 = 0xFFFFFFFF
    truth = np.empty(len(probabilities), dtype=np.uint8)
    for index, probability in enumerate(probabilities):
        p1 = int(probability)
        delta = x2 - x1
        midpoint = x1 + (delta >> 16) * p1 + (
            (delta & 0xFFFF) * p1 >> 16
        )
        if code <= midpoint:
            truth[index] = 1
            x2 = midpoint
        else:
            truth[index] = 0
            x1 = midpoint + 1
        while ((x1 ^ x2) & 0xFF000000) == 0:
            x1 = (x1 << 8) & 0xFFFFFFFF
            x2 = ((x2 << 8) & 0xFFFFFFFF) + 255
            next_byte = payload[cursor] if cursor < len(payload) else 0
            cursor += 1
            code = ((code << 8) & 0xFFFFFFFF) + next_byte
    return truth


def probability_logits(probabilities):
    import numpy as np

    p = np.clip(probabilities.astype(np.float64), 1, 65535) / 65536.0
    return np.log(p) - np.log1p(-p)


def quantized_probabilities(base_logits, residuals):
    import numpy as np

    logits = np.clip(base_logits + residuals, -20.0, 20.0)
    values = 65536.0 / (1.0 + np.exp(-logits))
    return np.clip(np.rint(values), 1, 65535).astype(np.uint16)


def fit_node_bias(base_logits, nodes, bits):
    import numpy as np

    logits = base_logits.reshape(-1).astype(np.float64)
    flat_nodes = nodes.reshape(-1).astype(np.int64)
    truth = bits.reshape(-1).astype(np.float64)
    residual = np.zeros(255, dtype=np.float64)
    for _ in range(12):
        adjusted = np.clip(logits + residual[flat_nodes], -20.0, 20.0)
        prediction = 1.0 / (1.0 + np.exp(-adjusted))
        gradient = np.bincount(
            flat_nodes, weights=prediction - truth, minlength=255
        )
        curvature = np.bincount(
            flat_nodes,
            weights=prediction * (1.0 - prediction),
            minlength=255,
        )
        step = gradient / np.maximum(curvature, 1e-9)
        residual -= np.clip(step, -2.0, 2.0)
        if float(np.max(np.abs(step))) < 1e-7:
            break
    return residual.astype(np.float32)


def serialize_jmdl1(quantized, scales) -> bytes:
    output = bytearray(b"JMDL1\0")
    names = sorted(quantized)
    output += struct.pack("<H", len(names))
    for name in names:
        encoded_name = name.encode("ascii")
        array = quantized[name]
        output += struct.pack("<H", len(encoded_name))
        output += encoded_name
        output += struct.pack("<B", array.ndim)
        for dimension in array.shape:
            output += struct.pack("<I", int(dimension))
        output += struct.pack("<f", float(scales[name]))
        output += array.astype("i1", copy=False).tobytes(order="C")
    return bytes(output)


def serialize_jbias1(values) -> bytes:
    return b"JBIAS1\0" + struct.pack("<H", len(values)) + values.astype(
        "<i2", copy=False
    ).tobytes(order="C")


def package_ledger(model_blob: bytes, decoder_allowance: int) -> dict:
    compressed = zlib.compress(model_blob, level=9)
    total = len(compressed) + decoder_allowance + OUTER_FRAME_BYTES
    return {
        "canonical_model_bytes": len(model_blob),
        "compressed_model_bytes": len(compressed),
        "decoder_allowance_bytes": decoder_allowance,
        "framing_bytes": OUTER_FRAME_BYTES,
        "other_data_bytes": 0,
        "total_package_bytes": total,
        "canonical_model_sha256": sha256_bytes(model_blob),
        "compressed_model_sha256": sha256_bytes(compressed),
    }


def select_projected_winner(
    baseline_bytes: int,
    j1_bytes: int,
    j2_bytes: int,
    j1_package: int,
    j2_package: int,
    raw_bytes: int,
) -> dict:
    scale = 1_000_000_000.0 / raw_bytes
    totals = {
        "J0": baseline_bytes * scale,
        "J1": j1_bytes * scale + j1_package,
        "J2": j2_bytes * scale + j2_package,
    }
    return {
        "projected_full_corpus_totals": totals,
        "winner": min(totals, key=totals.get),
    }


def result_exit_code(verdict: str) -> int:
    if verdict in {"AUTHORIZED_10M", "REJECT"}:
        return 0
    return 1


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p1", type=Path, default=DEFAULT_P1)
    parser.add_argument("--wrt", type=Path, default=DEFAULT_WRT)
    parser.add_argument("--raw-input", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--parent-archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument(
        "--inverse-receipt", type=Path, default=DEFAULT_INVERSE_RECEIPT
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("results/janus_paid_residual_mdl_1m_v2"),
    )
    parser.add_argument("--raw-bytes", type=int, default=1_000_000)
    parser.add_argument("--expected-parent-payload", type=int, default=173_859)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_rocm()

    import numpy as np
    import torch
    from torch import nn

    seed = 428
    block_size = 256
    batch_size = 32
    epochs = 8
    if not torch.cuda.is_available():
        raise SystemExit("receipt-bound ROCm PyTorch has no visible GPU")
    device = torch.device("cuda")
    args.results.mkdir(parents=True, exist_ok=False)

    wrt_raw = args.wrt.read_bytes()
    if len(wrt_raw) <= 5:
        raise ValueError("WRT store is missing its five-byte header")
    wrt = np.frombuffer(wrt_raw, dtype=np.uint8, offset=5).copy()
    p1_magic, p1 = read_p1(args.p1, len(wrt) * 8)
    all_truth = np.unpackbits(wrt, bitorder="big")

    parent_payload = range_encode(p1, all_truth)
    if len(parent_payload) != args.expected_parent_payload:
        raise ValueError("exact parent payload length mismatch")
    archive = args.parent_archive.read_bytes()
    if len(archive) < len(parent_payload):
        raise ValueError("parent archive is shorter than its payload")
    receipt_parent_payload = archive[-len(parent_payload) :]
    if parent_payload != receipt_parent_payload:
        raise ValueError("parent payload byte identity failed")

    raw_sha256 = sha256_file(args.raw_input)
    wrt_sha256 = sha256_file(args.wrt)
    inverse_text = args.inverse_receipt.read_text(encoding="utf-8")
    inverse_bound = raw_sha256 in inverse_text and wrt_sha256 in inverse_text
    if not inverse_bound:
        raise ValueError("WRT-to-raw inverse receipt does not bind inputs")

    complete_bytes = (len(wrt) // block_size) * block_size
    block_count = complete_bytes // block_size
    if block_count < 20:
        raise ValueError("population has too few complete blocks")
    tail_bytes = len(wrt) - complete_bytes
    wrt_blocks = wrt[:complete_bytes].reshape(block_count, block_size)
    p1_blocks = p1[: complete_bytes * 8].reshape(
        block_count, block_size, 8
    )
    bits = np.unpackbits(wrt_blocks[..., None], axis=2, bitorder="big")
    nodes = np.empty((block_count, block_size, 8), dtype=np.uint16)
    for bit_position in range(8):
        prefix = (
            np.zeros_like(wrt_blocks, dtype=np.uint16)
            if bit_position == 0
            else wrt_blocks.astype(np.uint16) >> (8 - bit_position)
        )
        nodes[:, :, bit_position] = (1 << bit_position) - 1 + prefix
    inputs = np.empty((block_count, block_size), dtype=np.int64)
    inputs[:, 0] = 256
    inputs[:, 1:] = wrt_blocks[:, :-1]
    base_logits = probability_logits(p1_blocks).astype(np.float32)

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

    def fit_once(run_index: int) -> dict:
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True

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
            truth = torch.from_numpy(bits[indices].astype(np.float32)).to(
                device
            )
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
                f"run={run_index} epoch={epoch + 1} "
                f"training={mean_loss:.8f}",
                flush=True,
            )

        quantized = {}
        scales = {}
        dequantized_state = {}
        for name, tensor in model.state_dict().items():
            array = tensor.detach().cpu().numpy().astype(np.float32)
            maximum = float(np.max(np.abs(array)))
            scale = maximum / 127.0 if maximum > 0.0 else 1.0
            values = np.clip(
                np.rint(array / scale), -127, 127
            ).astype(np.int8)
            quantized[name] = values
            scales[name] = np.float32(scale)
            dequantized_state[name] = torch.from_numpy(
                values.astype(np.float32) * np.float32(scale)
            )
        model_blob = serialize_jmdl1(quantized, scales)
        model.load_state_dict(dequantized_state)
        model.to(device)
        model.eval()

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

        adjusted = quantized_probabilities(
            base_logits, selected_residuals
        ).reshape(-1)
        candidate_p1 = p1.copy()
        candidate_p1[: complete_bytes * 8] = adjusted
        candidate_payload = range_encode(candidate_p1, all_truth)
        decoded = range_decode(candidate_payload, candidate_p1)
        if not np.array_equal(decoded, all_truth):
            raise ValueError("candidate arithmetic decode failed")
        return {
            "model_blob": model_blob,
            "candidate_p1": candidate_p1,
            "candidate_payload": candidate_payload,
            "epoch_receipts": epoch_receipts,
            "parameter_count": sum(
                parameter.numel() for parameter in model.parameters()
            ),
        }

    run_a = fit_once(1)
    run_b = fit_once(2)
    determinism = {
        "model_blob_identity": run_a["model_blob"] == run_b["model_blob"],
        "adjusted_p1_identity": np.array_equal(
            run_a["candidate_p1"], run_b["candidate_p1"]
        ),
        "candidate_payload_identity": (
            run_a["candidate_payload"] == run_b["candidate_payload"]
        ),
        "training_metrics_identity": (
            run_a["epoch_receipts"] == run_b["epoch_receipts"]
        ),
    }
    if not all(determinism.values()):
        raise ValueError("A/B deterministic training identity failed")

    model_blob = run_a["model_blob"]
    compressed_model = zlib.compress(model_blob, level=9)
    (args.results / "janus_jmdl1.bin").write_bytes(model_blob)
    (args.results / "janus_jmdl1.zlib").write_bytes(compressed_model)
    (args.results / "janus_candidate.payload").write_bytes(
        run_a["candidate_payload"]
    )

    node_bias = fit_node_bias(base_logits, nodes, bits)
    bias_q10 = np.clip(
        np.rint(node_bias * 1024.0), -32768, 32767
    ).astype(np.int16)
    bias_residual = bias_q10.astype(np.float32) / 1024.0
    bias_adjusted = quantized_probabilities(
        base_logits, bias_residual[nodes]
    ).reshape(-1)
    bias_p1 = p1.copy()
    bias_p1[: complete_bytes * 8] = bias_adjusted
    bias_payload = range_encode(bias_p1, all_truth)
    if not np.array_equal(range_decode(bias_payload, bias_p1), all_truth):
        raise ValueError("J1 arithmetic decode failed")
    bias_blob = serialize_jbias1(bias_q10)
    (args.results / "janus_jbias1.bin").write_bytes(bias_blob)
    (args.results / "janus_jbias1.zlib").write_bytes(
        zlib.compress(bias_blob, level=9)
    )
    (args.results / "janus_bias.payload").write_bytes(bias_payload)

    adjusted_rows = run_a["candidate_p1"][: complete_bytes * 8].reshape(
        complete_bytes, 8
    )
    shifted_rows = np.roll(
        adjusted_rows, shift=4093, axis=0
    )
    shifted_p1 = p1.copy()
    shifted_p1[: complete_bytes * 8] = shifted_rows.reshape(-1)
    shifted_payload = range_encode(shifted_p1, all_truth)

    baseline_bytes = len(parent_payload)
    j1_bytes = len(bias_payload)
    j2_bytes = len(run_a["candidate_payload"])
    shifted_bytes = len(shifted_payload)
    j1_gain = baseline_bytes - j1_bytes
    j2_gain = baseline_bytes - j2_bytes
    shifted_gain = baseline_bytes - shifted_bytes

    j1_package = package_ledger(bias_blob, J1_DECODER_ALLOWANCE)
    j2_package = package_ledger(model_blob, J2_DECODER_ALLOWANCE)
    selection = select_projected_winner(
        baseline_bytes,
        j1_bytes,
        j2_bytes,
        j1_package["total_package_bytes"],
        j2_package["total_package_bytes"],
        args.raw_bytes,
    )
    j1_gross_bpm = j1_gain * 1_000_000.0 / args.raw_bytes
    j2_gross_bpm = j2_gain * 1_000_000.0 / args.raw_bytes
    j1_net_bpm = (
        j1_gross_bpm - j1_package["total_package_bytes"] / 1000.0
    )
    j2_net_bpm = (
        j2_gross_bpm - j2_package["total_package_bytes"] / 1000.0
    )
    j1_authorized = (
        j1_gross_bpm >= 3000.0
        and j1_net_bpm >= 2100.0
        and j1_package["total_package_bytes"] <= PACKAGE_CEILING
        and selection["winner"] == "J1"
    )
    j2_authorized = (
        j2_gross_bpm >= 3000.0
        and j2_net_bpm >= 2100.0
        and j2_gain > shifted_gain
        and j2_package["total_package_bytes"] <= PACKAGE_CEILING
        and selection["winner"] == "J2"
    )
    authorized = j1_authorized or j2_authorized
    promoted = "J1" if j1_authorized else "J2" if j2_authorized else None

    oracle_harness_bytes = len(
        zlib.compress(
            Path(__file__).read_bytes()
            + Path(__file__).with_name(
                "chiron_residual_oracle.py"
            ).read_bytes(),
            level=9,
        )
    )
    decision = {
        "schema": "gamma.janus_paid_residual_mdl_oracle.v2",
        "candidate": "janus_paid_residual_mdl_q0_v1",
        "verdict": "AUTHORIZED_10M" if authorized else "REJECT",
        "promoted_control": promoted,
        "score_credit_bytes": 0,
        "inputs": {
            "p1_path": str(args.p1),
            "p1_sha256": sha256_file(args.p1),
            "p1_magic_hex": p1_magic,
            "wrt_path": str(args.wrt),
            "wrt_sha256": wrt_sha256,
            "raw_path": str(args.raw_input),
            "raw_sha256": raw_sha256,
            "inverse_receipt": str(args.inverse_receipt),
            "inverse_receipt_sha256": sha256_file(args.inverse_receipt),
            "raw_bytes": args.raw_bytes,
            "wrt_bytes": len(wrt),
            "complete_wrt_bytes": complete_bytes,
            "tail_wrt_bytes": tail_bytes,
            "parent_archive": str(args.parent_archive),
            "parent_archive_sha256": sha256_file(args.parent_archive),
        },
        "architecture": {
            "block_size": block_size,
            "embedding_width": 64,
            "hidden_width": 96,
            "gru_layers": 2,
            "readout_nodes": 255,
            "epochs": epochs,
            "batch_size": batch_size,
            "seed": seed,
            "parameter_count": run_a["parameter_count"],
            "selection": "fixed final epoch",
            "quantization": "symmetric signed int8 per tensor",
            "runtime_oracle": "dequantized float32 ROCm",
        },
        "exact_bytes": {
            "J0_parent": baseline_bytes,
            "J1_node_bias": j1_bytes,
            "J1_gain": j1_gain,
            "J2_gru": j2_bytes,
            "J2_gain": j2_gain,
            "JS_shifted": shifted_bytes,
            "JS_gain": shifted_gain,
        },
        "payload_hashes": {
            "J0": sha256_bytes(parent_payload),
            "J1": sha256_bytes(bias_payload),
            "J2": sha256_bytes(run_a["candidate_payload"]),
            "JS": sha256_bytes(shifted_payload),
            "adjusted_p1": sha256_bytes(
                run_a["candidate_p1"].astype("<u2").tobytes()
            ),
        },
        "package": {
            "J1": j1_package,
            "J2": j2_package,
            "oracle_harness_compressed_bytes": oracle_harness_bytes,
            "oracle_harness_is_not_decoder_charge": True,
            "package_ceiling_bytes": PACKAGE_CEILING,
        },
        "economics": {
            "J1_gross_bytes_per_million": j1_gross_bpm,
            "J1_net_bytes_per_million": j1_net_bpm,
            "J2_gross_bytes_per_million": j2_gross_bpm,
            "J2_net_bytes_per_million": j2_net_bpm,
            "literal_population_totals": {
                "J0": baseline_bytes,
                "J1": j1_bytes + j1_package["total_package_bytes"],
                "J2": j2_bytes + j2_package["total_package_bytes"],
            },
            **selection,
        },
        "proof": {
            "parent_payload_identity": (
                parent_payload == receipt_parent_payload
            ),
            "full_candidate_arithmetic_decode": True,
            "full_J1_arithmetic_decode": True,
            "tail_uses_parent_p1": np.array_equal(
                run_a["candidate_p1"][complete_bytes * 8 :],
                p1[complete_bytes * 8 :],
            ),
            "wrt_raw_inverse_bound": inverse_bound,
            "A_B_determinism": determinism,
        },
        "gates": {
            "J1_authorized": j1_authorized,
            "J2_authorized": j2_authorized,
            "J2_beats_shift": j2_gain > shifted_gain,
            "J2_beats_J1_projected_total": (
                selection["projected_full_corpus_totals"]["J2"]
                < selection["projected_full_corpus_totals"]["J1"]
            ),
            "J2_package_within_ceiling": (
                j2_package["total_package_bytes"] <= PACKAGE_CEILING
            ),
        },
        "training_A": run_a["epoch_receipts"],
        "training_B": run_b["epoch_receipts"],
        "limitations": [
            "Training and evaluation use the same fixed population.",
            "The GRU runtime remains a dequantized ROCm oracle.",
            "Decoder allowances are frozen research accounting bounds.",
            "No deterministic integer decoder exists.",
            "Full-corpus economics are an amortization screen, not score proof.",
            "This receipt has zero forecast and score credit.",
        ],
    }
    (args.results / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision["exact_bytes"], sort_keys=True), flush=True)
    print(json.dumps(decision["economics"], sort_keys=True), flush=True)
    print(f"verdict={decision['verdict']}", flush=True)
    return result_exit_code(decision["verdict"])


if __name__ == "__main__":
    raise SystemExit(main())
