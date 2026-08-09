#!/usr/bin/env python3
"""Frozen H32+H96 rich-state residual-capacity gate for cmix-obias.

The paid H128 arm is represented as a block-diagonal 128-cell LSTM: the
receipt-bound frozen H32 donor head plus one independently trained H96 residual
branch.  This starts bit-exactly at H32 and isolates incremental capacity.  It
is a diagnostic ceiling, not a submission codec.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import pathlib
import struct
import sys
import types
import zlib

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

try:
    from numba import njit
except ModuleNotFoundError:
    # The lab's system Python omits numba.  The diagnostic populations are
    # deliberately small, so the donor's two @njit helpers remain correct as
    # ordinary Python functions.  Publish a minimal module before importing
    # the donor feature builder, which also uses ``from numba import njit``.
    def njit(function=None, **_kwargs):
        if function is None:
            return lambda wrapped: wrapped
        return function

    numba_stub = types.ModuleType("numba")
    numba_stub.njit = njit
    sys.modules["numba"] = numba_stub


CANDIDATE_ID = "cmix_richstate_lstm128_ceiling_qm0_v1"
BLOCK_BITS = 1 << 20
TRAIN_BLOCK = 0
DEV_BLOCK = 1
CONFIRM_BLOCKS = (2, 3, 4)
SEQUENCE_BITS = 64
SEED = 20260808
LEARNING_RATE = 5e-4
REQUIRED_BYTES_PER_MODELED_MB = 7816.0
FULL_MODELED_BYTES = 587_138_826
PARENT_DEBT_BYTES = 3_492_825
RESERVE_BYTES = 500_000
SOURCE_ALLOWANCE_BYTES = 65_000


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(8 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: pathlib.Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def parameter_count(hidden: int) -> int:
    return 8 * hidden * hidden + 103 * hidden + 1


def blob_bytes(hidden: int) -> int:
    return 24 + 2 * parameter_count(hidden)


class ResidualLSTM(nn.Module):
    def __init__(self, hidden: int):
        super().__init__()
        self.in_proj = nn.Linear(93, hidden)
        self.lstm = nn.LSTM(hidden, hidden, batch_first=True)
        self.out = nn.Linear(hidden, 1)
        nn.init.zeros_(self.out.weight)
        nn.init.zeros_(self.out.bias)

    def forward(self, x: torch.Tensor, previous_bit: torch.Tensor) -> torch.Tensor:
        h = F.silu(self.in_proj(torch.cat((x, previous_bit[..., None]), -1)))
        h, _ = self.lstm(h)
        return self.out(h).squeeze(-1)


def load_fp16_h32(blob_path: pathlib.Path, lstm_class) -> nn.Module:
    raw = blob_path.read_bytes()
    if len(raw) != 23_002 or raw[:8] != b"KHBL32\x02\x00":
        raise RuntimeError("unexpected H32 fp16 blob")
    nin, hidden, reset, reserved = struct.unpack_from("<IIII", raw, 8)
    if (nin, hidden, reset, reserved) != (92, 32, 64, 0):
        raise RuntimeError("unexpected H32 blob header")
    shapes = (
        ("in_proj.weight", (32, 93)),
        ("in_proj.bias", (32,)),
        ("lstm.weight_ih_l0", (128, 32)),
        ("lstm.weight_hh_l0", (128, 32)),
        ("lstm.bias_ih_l0", (128,)),
        ("lstm.bias_hh_l0", (128,)),
        ("out.weight", (1, 32)),
        ("out.bias", (1,)),
    )
    offset = 24
    state = {}
    for name, shape in shapes:
        count = math.prod(shape)
        array = np.frombuffer(raw, dtype="<f2", count=count, offset=offset)
        state[name] = torch.from_numpy(array.astype(np.float32).reshape(shape).copy())
        offset += 2 * count
    if offset != len(raw):
        raise RuntimeError("H32 blob payload length mismatch")
    model = lstm_class(92, 32, SEQUENCE_BITS)
    model.load_state_dict(state)
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    return model


def fp16_roundtrip(model: nn.Module) -> None:
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.copy_(parameter.half().float())


def build_coded_stream(bytes_path: pathlib.Path, output: pathlib.Path) -> None:
    record = np.dtype([("byte", "u1"), ("bits", "<f4")])
    rows = np.memmap(bytes_path, dtype=record, mode="r")
    np.asarray(rows["byte"]).tofile(output)


def prepare_block(source, block_index: int, device: torch.device):
    visit = source.order.index(block_index)
    data = source.get(visit, device)
    offset = data["offset"]
    count = data["count"]
    x = data["x"][offset:offset + count].clone()
    x[:, 69:75] = 0
    t = data["t"][offset:offset + count]
    y = data["y"][offset:offset + count]
    w = data["w"][offset:offset + count]
    previous = torch.empty_like(y)
    previous[0] = 0.5 if data["start"] == 0 else data["y"][offset - 1]
    previous[1:] = y[:-1]
    if count % SEQUENCE_BITS:
        raise RuntimeError("block is not sequence aligned")
    nseq = count // SEQUENCE_BITS
    return {
        "start": data["start"],
        "count": count,
        "x": x.view(nseq, SEQUENCE_BITS, 92),
        "t": t.view(nseq, SEQUENCE_BITS),
        "y": y.view(nseq, SEQUENCE_BITS),
        "w": w.view(nseq, SEQUENCE_BITS),
        "previous": previous.view(nseq, SEQUENCE_BITS),
        "base_p": data["rec"]["final_p"][offset:offset + count].astype(np.uint16).copy(),
    }


def train_residual(base: nn.Module, residual: nn.Module, block: dict, batch_sequences: int) -> dict:
    residual.train()
    optimizer = torch.optim.AdamW(residual.parameters(), lr=LEARNING_RATE, weight_decay=0)
    generator = torch.Generator(device="cpu").manual_seed(SEED)
    order = torch.randperm(len(block["x"]), generator=generator)
    total_loss = 0.0
    total_weight = 0.0
    for begin in range(0, len(order), batch_sequences):
        indices = order[begin:begin + batch_sequences]
        x = block["x"][indices]
        t = block["t"][indices]
        y = block["y"][indices]
        w = block["w"][indices]
        previous = block["previous"][indices]
        with torch.no_grad():
            h32_logit = base(x, t, previous)
        logit = h32_logit + residual(x, previous)
        losses = F.binary_cross_entropy_with_logits(logit, y, reduction="none")
        denominator = w.sum().clamp(min=1)
        loss = (losses * w).sum() / denominator
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(residual.parameters(), 1.0)
        optimizer.step()
        total_loss += float((losses.detach() * w).double().sum())
        total_weight += float(denominator)
    residual.eval()
    return {"weighted_nats": total_loss, "weighted_bits": total_loss / math.log(2), "bits": total_weight}


@torch.no_grad()
def predict_probabilities(base: nn.Module, residual: nn.Module, block: dict, batch_sequences: int):
    base_probabilities = block["base_p"].copy()
    h32_parts = []
    h128_parts = []
    for begin in range(0, len(block["x"]), batch_sequences):
        stop = begin + batch_sequences
        x = block["x"][begin:stop]
        t = block["t"][begin:stop]
        previous = block["previous"][begin:stop]
        h32_logit = base(x, t, previous)
        h128_logit = h32_logit + residual(x, previous)
        for logit, parts in ((h32_logit, h32_parts), (h128_logit, h128_parts)):
            probability = torch.sigmoid(logit.float())
            discretized = (1.0 + 65534.0 * probability).to(torch.int64)
            parts.append(discretized.flatten().cpu().numpy().astype(np.uint16))
    h32 = np.concatenate(h32_parts)
    h128 = np.concatenate(h128_parts)
    override = block["w"].flatten().cpu().numpy() == 0
    h32[override] = base_probabilities[override]
    h128[override] = base_probabilities[override]
    truth = block["y"].flatten().cpu().numpy().astype(np.uint8)
    return base_probabilities, h32, h128, truth


def ideal_bytes(probability: np.ndarray, truth: np.ndarray) -> float:
    numerator = np.where(truth != 0, probability.astype(np.float64),
                         65536.0 - probability.astype(np.float64))
    return float(-np.log2(numerator / 65536.0).sum() / 8.0)


@njit(cache=True)
def range_bytes(probability, truth):
    x1 = np.uint64(0)
    x2 = np.uint64(0xFFFFFFFF)
    mask = np.uint64(0xFFFFFFFF)
    output = 0
    for index in range(len(probability)):
        p = np.uint64(probability[index])
        width = x2 - x1
        midpoint = x1 + (width >> np.uint64(16)) * p + (((width & np.uint64(0xFFFF)) * p) >> np.uint64(16))
        if truth[index] != 0:
            x2 = midpoint
        else:
            x1 = midpoint + np.uint64(1)
        while ((x1 ^ x2) & np.uint64(0xFF000000)) == 0:
            output += 1
            x1 = (x1 << np.uint64(8)) & mask
            x2 = ((x2 << np.uint64(8)) + np.uint64(255)) & mask
    while ((x1 ^ x2) & np.uint64(0xFF000000)) == 0:
        output += 1
        x1 = (x1 << np.uint64(8)) & mask
        x2 = ((x2 << np.uint64(8)) + np.uint64(255)) & mask
    return output + 1


def score_block(base: nn.Module, residual: nn.Module, block: dict, batch_sequences: int) -> dict:
    p0, p32, p128, truth = predict_probabilities(base, residual, block, batch_sequences)
    ideal = {"B0": ideal_bytes(p0, truth), "H32": ideal_bytes(p32, truth), "H128": ideal_bytes(p128, truth)}
    finite = {"B0": int(range_bytes(p0, truth)), "H32": int(range_bytes(p32, truth)), "H128": int(range_bytes(p128, truth))}
    return {
        "start_bit": block["start"],
        "bits": block["count"],
        "modeled_bytes": block["count"] // 8,
        "ideal_bytes": ideal,
        "finite_range_bytes": finite,
        "h128_minus_h32_gain_ideal_bytes": ideal["H32"] - ideal["H128"],
        "h128_minus_h32_gain_finite_bytes": finite["H32"] - finite["H128"],
        "h32_minus_base_gain_ideal_bytes": ideal["B0"] - ideal["H32"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--donor-root", type=pathlib.Path, required=True)
    parser.add_argument("--trace-prefix", type=pathlib.Path, required=True)
    parser.add_argument("--work-dir", type=pathlib.Path, required=True)
    parser.add_argument("--output-dir", type=pathlib.Path, required=True)
    parser.add_argument("--threads", type=int, default=min(32, os.cpu_count() or 1))
    parser.add_argument("--batch-sequences", type=int, default=512)
    args = parser.parse_args()

    torch.set_num_threads(args.threads)
    torch.manual_seed(SEED)
    donor_root = args.donor_root.resolve()
    trace_prefix = args.trace_prefix.resolve()
    trace_path = pathlib.Path(str(trace_prefix) + ".res")
    bytes_path = pathlib.Path(str(trace_prefix) + ".bytes")
    meta_path = pathlib.Path(str(trace_prefix) + ".meta")
    head_path = donor_root / "models" / "bitlstm32" / "refit_golden256_fp16.blob"
    for path in (trace_path, bytes_path, meta_path, head_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    meta = meta_path.read_text()
    if "format=res_v3" not in meta or "truncated=0" not in meta:
        raise RuntimeError("trace is not a complete res_v3 stream")
    needed_bits = (max(CONFIRM_BLOCKS) + 1) * BLOCK_BITS
    record_count = trace_path.stat().st_size // 56
    if record_count < needed_bits:
        raise RuntimeError(f"trace has {record_count} records; need {needed_bits}")

    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    coded_stream = args.work_dir / "coded_stream.bin"
    build_coded_stream(bytes_path, coded_stream)

    head_refit = donor_root / "tools" / "head_refit"
    sys.path.insert(0, str(head_refit))
    from continuous_shuffled_lstm import LSTMHead  # type: ignore
    from shuffled_blocks import ShuffledBlockSource  # type: ignore

    device = torch.device("cpu")
    base = load_fp16_h32(head_path, LSTMHead).to(device)
    residual = ResidualLSTM(96).to(device)
    source = ShuffledBlockSource(str(trace_path), str(coded_stream), needed_bits,
                                 BLOCK_BITS, BLOCK_BITS, SEED)
    source.coverage_assertions()
    try:
        training = prepare_block(source, TRAIN_BLOCK, device)
        training_receipt = train_residual(base, residual, training, args.batch_sequences)
        fp16_roundtrip(residual)
        development = score_block(base, residual, prepare_block(source, DEV_BLOCK, device), args.batch_sequences)
        confirmation = [score_block(base, residual, prepare_block(source, block, device), args.batch_sequences)
                        for block in CONFIRM_BLOCKS]
    finally:
        source.close()

    confirmation_bytes = sum(row["modeled_bytes"] for row in confirmation)
    ideal_gain = sum(row["h128_minus_h32_gain_ideal_bytes"] for row in confirmation)
    finite_gain = sum(row["h128_minus_h32_gain_finite_bytes"] for row in confirmation)
    rate = finite_gain * 1_000_000.0 / confirmation_bytes
    projected_full_gross = rate * FULL_MODELED_BYTES / 1_000_000.0
    h32_blob = blob_bytes(32)
    h128_blob = blob_bytes(128)
    twice_incremental_model = 2 * (h128_blob - h32_blob)
    required_full_gross = (PARENT_DEBT_BYTES + RESERVE_BYTES + SOURCE_ALLOWANCE_BYTES
                           + twice_incremental_model)
    all_thirds_positive = all(row["h128_minus_h32_gain_finite_bytes"] > 0 for row in confirmation)
    promotion = rate >= REQUIRED_BYTES_PER_MODELED_MB and all_thirds_positive

    source_bytes = pathlib.Path(__file__).read_bytes()
    decision = {
        "schema": "cmix_richstate_lstm128_ceiling_qm0_decision_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "PROMOTE_NATIVE_H128" if promotion else "RETIRED_NEGATIVE",
        "claim_boundary": "Exact local res_v3 same-object finite range replay on five opening 1-Mbit blocks. This is a capacity gate, not a full cmix archive or prize score.",
        "population": {
            "record_count": record_count,
            "trace_bytes": trace_path.stat().st_size,
            "trace_sha256": sha256_file(trace_path),
            "bytes_tier_sha256": sha256_file(bytes_path),
            "coded_stream_bytes": coded_stream.stat().st_size,
            "train_block": TRAIN_BLOCK,
            "development_block": DEV_BLOCK,
            "confirmation_blocks": list(CONFIRM_BLOCKS),
        },
        "model": {
            "construction": "frozen external H32 plus trained block-diagonal H96 residual, equivalent to a sparse H128 cell",
            "seed": SEED,
            "epochs": 1,
            "learning_rate": LEARNING_RATE,
            "sequence_reset_bits": SEQUENCE_BITS,
            "h32_parameters": parameter_count(32),
            "h128_dense_parameters_charged": parameter_count(128),
            "h32_blob_bytes": h32_blob,
            "h128_dense_blob_bytes_charged": h128_blob,
            "twice_incremental_model_bytes": twice_incremental_model,
            "head_blob_sha256": sha256_file(head_path),
            "training": training_receipt,
        },
        "development": development,
        "confirmation": confirmation,
        "aggregate": {
            "confirmation_modeled_bytes": confirmation_bytes,
            "h128_minus_h32_gain_ideal_bytes": ideal_gain,
            "h128_minus_h32_gain_finite_bytes": finite_gain,
            "gain_bytes_per_modeled_mb": rate,
            "required_bytes_per_modeled_mb": REQUIRED_BYTES_PER_MODELED_MB,
            "rate_margin": rate - REQUIRED_BYTES_PER_MODELED_MB,
            "all_confirmation_thirds_positive": all_thirds_positive,
            "projected_full_gross_bytes": projected_full_gross,
            "required_full_gross_bytes": required_full_gross,
            "projected_full_margin_bytes": projected_full_gross - required_full_gross,
        },
        "accounting": {
            "parent_debt_bytes": PARENT_DEBT_BYTES,
            "reserve_bytes": RESERVE_BYTES,
            "source_allowance_bytes": SOURCE_ALLOWANCE_BYTES,
            "compressed_tool_source_bytes": len(zlib.compress(source_bytes, 9)),
            "models_charged_twice": True,
        },
        "promotion": promotion,
        "next_action": ("Materialize one native H128 donor child and measure an exact complete archive."
                        if promotion else
                        "Retire wider rich-state residual heads without hidden-width, reset, feature, optimizer, or epoch rescue sweeps."),
    }
    atomic_json(args.output_dir / "decision.json", decision)
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
