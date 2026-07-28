#!/usr/bin/env python3
"""Run the bounded ROCm-native causal teacher Q0 construction gate."""

from __future__ import annotations

import argparse
from array import array
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import struct
import subprocess
import sys
import time

ROCM_PYTHON = Path(
    "/home/x/enwiki9-nonproof/external/rocm-pytorch-venv/bin/python"
)
if Path(sys.executable) != ROCM_PYTHON:
    if not ROCM_PYTHON.is_file():
        raise SystemExit(f"missing receipt-bound ROCm interpreter: {ROCM_PYTHON}")
    os.execv(str(ROCM_PYTHON), [str(ROCM_PYTHON), *sys.argv])

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


PROBABILITY_BITS = 15
PROBABILITY_TOTAL = 1 << PROBABILITY_BITS
RANGE_MIN_BITS = 16
RANGE_MIN = (0xFF << (RANGE_MIN_BITS - 8)) + 1
RANGE_MAX = 0xFF << RANGE_MIN_BITS
TRACE_MAGIC = b"RQ0TR1\0\0"


@dataclass(frozen=True)
class Config:
    vocabulary: int = 16392
    layers: int = 20
    width: int = 1024
    heads: int = 8
    head_width: int = 128
    inner_width: int = 3072
    segment_length: int = 64
    memory_length: int = 256
    learning_rate: float = 0.00016
    adam_beta1: float = 0.0
    adam_beta2: float = 0.9999
    adam_epsilon: float = 1e-8
    gradient_clip: float = 0.05
    seed: int = 123


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


class RangeEncoder:
    def __init__(self) -> None:
        self.low = 0
        self.range = RANGE_MAX
        self.current_byte = 0xFF
        self.pending_bytes = 0
        self.output = bytearray()

    def _put_value(self, value: int) -> None:
        if value == 0xFF:
            self.pending_bytes += 1
            return
        if self.pending_bytes:
            carry = value >> 8
            self.output.append((self.current_byte + carry) & 0xFF)
            fill = (0xFF + carry) & 0xFF
            while self.pending_bytes > 1:
                self.output.append(fill)
                self.pending_bytes -= 1
        self.pending_bytes = 1
        self.current_byte = value

    def put_bit(self, probability_zero: int, bit: int) -> None:
        split = (self.range * probability_zero) >> PROBABILITY_BITS
        if not 0 < split < self.range:
            raise ValueError("invalid range split")
        if bit:
            self.low += split
            self.range -= split
        else:
            self.range = split
        while self.range < RANGE_MIN:
            self._put_value(self.low >> RANGE_MIN_BITS)
            self.low = (self.low & ((1 << RANGE_MIN_BITS) - 1)) << 8
            self.range <<= 8

    def finish(self) -> bytes:
        if self.range < (1 << RANGE_MIN_BITS):
            self._put_value(self.low >> RANGE_MIN_BITS)
            self.low = (self.low & ((1 << RANGE_MIN_BITS) - 1)) << 8
            self.range <<= 8
        width = 0
        while (1 << (width + 1)) <= self.range:
            width += 1
        value = self.low
        mask = (1 << width) - 1
        if value & mask:
            value = (value + (1 << width)) & ~mask
        if not self.low <= value < self.low + self.range:
            raise ValueError("range finalization failed")
        self._put_value(value >> RANGE_MIN_BITS)
        if self.pending_bytes:
            self._put_value(0)
        return bytes(self.output)


class RangeDecoder:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.index = 0
        self.low = 0
        self.range = 0
        for _ in range(0, RANGE_MIN_BITS + 1, 8):
            self._refill()
        self.range = RANGE_MAX

    def _refill(self) -> None:
        self.range <<= 8
        self.low <<= 8
        if self.index < len(self.payload):
            self.low += self.payload[self.index]
            self.index += 1

    def get_bit(self, probability_zero: int) -> int:
        split = (self.range * probability_zero) >> PROBABILITY_BITS
        if not 0 < split < self.range:
            raise ValueError("invalid decode split")
        bit = int(self.low >= split)
        if bit:
            self.low -= split
            self.range -= split
        else:
            self.range = split
        while self.range < RANGE_MIN:
            self._refill()
        return bit


class RMSNorm(nn.Module):
    def __init__(self, width: int) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.ones(width))

    def forward(self, value: torch.Tensor) -> torch.Tensor:
        scale = torch.rsqrt(
            value.float().square().mean(dim=-1, keepdim=True) + 1e-8
        )
        return value * scale.to(value.dtype) * self.weight.to(value.dtype)


class CausalBlock(nn.Module):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
        width = config.width
        heads_width = config.heads * config.head_width
        self.attention_norm = RMSNorm(width)
        self.feedforward_norm = RMSNorm(width)
        self.query = nn.Linear(width, heads_width, bias=False)
        self.key = nn.Linear(width, heads_width, bias=False)
        self.value = nn.Linear(width, heads_width, bias=False)
        self.output = nn.Linear(heads_width, width, bias=False)
        self.feedforward_in = nn.Linear(width, config.inner_width * 2)
        self.feedforward_out = nn.Linear(config.inner_width, width)

    def forward(
        self, value: torch.Tensor, memory: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        config = self.config
        batch, length, _ = value.shape
        normalized = self.attention_norm(value)
        history = torch.cat((memory, normalized), dim=1)
        memory_length = memory.shape[1]
        keys_length = history.shape[1]

        query = self.query(normalized).view(
            batch, length, config.heads, config.head_width
        ).transpose(1, 2)
        key = self.key(history).view(
            batch, keys_length, config.heads, config.head_width
        ).transpose(1, 2)
        projected_value = self.value(history).view(
            batch, keys_length, config.heads, config.head_width
        ).transpose(1, 2)
        score = torch.matmul(query, key.transpose(-1, -2)).float()
        score /= math.sqrt(config.head_width)

        query_position = torch.arange(length, device=value.device)[:, None]
        key_position = torch.arange(keys_length, device=value.device)[None, :]
        distance = memory_length + query_position - key_position
        allowed = distance >= 0
        slopes = torch.pow(
            torch.tensor(2.0, device=value.device),
            -8.0
            * (
                torch.arange(config.heads, device=value.device).float() + 1.0
            )
            / config.heads,
        )
        score -= slopes[None, :, None, None] * distance.clamp_min(0)[
            None, None, :, :
        ]
        score = score.masked_fill(~allowed[None, None, :, :], -1e30)
        probability = torch.softmax(score, dim=-1).to(projected_value.dtype)
        attended = torch.matmul(probability, projected_value)
        attended = attended.transpose(1, 2).reshape(
            batch, length, config.heads * config.head_width
        )
        value = value + self.output(attended)
        normalized_ff = self.feedforward_norm(value)
        gate, content = self.feedforward_in(normalized_ff).chunk(2, dim=-1)
        value = value + self.feedforward_out(F.gelu(gate) * content)
        next_memory = history[:, -config.memory_length :, :].detach()
        return value, next_memory


class RocmTeacher(nn.Module):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
        self.embedding = nn.Embedding(config.vocabulary, config.width)
        self.blocks = nn.ModuleList(
            CausalBlock(config) for _ in range(config.layers)
        )
        self.final_norm = RMSNorm(config.width)
        self.readout = nn.Linear(config.width, config.vocabulary)
        self.reset_parameters()

    def reset_parameters(self) -> None:
        for parameter in self.parameters():
            if parameter.ndim >= 2:
                nn.init.uniform_(parameter, -0.01, 0.01)
            else:
                nn.init.zeros_(parameter)
        for module in self.modules():
            if isinstance(module, RMSNorm):
                nn.init.ones_(module.weight)

    def empty_memory(
        self, device: torch.device, dtype: torch.dtype
    ) -> list[torch.Tensor]:
        return [
            torch.empty(1, 0, self.config.width, device=device, dtype=dtype)
            for _ in self.blocks
        ]

    def forward(
        self, symbols: torch.Tensor, memories: list[torch.Tensor]
    ) -> tuple[torch.Tensor, list[torch.Tensor]]:
        value = self.embedding(symbols).to(torch.bfloat16)
        value *= math.sqrt(self.config.width)
        next_memories: list[torch.Tensor] = []
        for block, memory in zip(self.blocks, memories, strict=True):
            value, next_memory = block(value, memory)
            next_memories.append(next_memory)
        value = self.final_norm(value)
        return self.readout(value).float(), next_memories


def probability_zero(
    cumulative: np.ndarray,
    start: int,
    left: int,
    active_mass: float,
) -> tuple[int, float]:
    end = start + left
    left_mass = float(cumulative[end - 1])
    if start:
        left_mass -= float(cumulative[start - 1])
    value = round(left_mass * PROBABILITY_TOTAL / active_mass)
    return min(max(value, 1), PROBABILITY_TOTAL - 1), left_mass


def encode_distribution(
    encoder: RangeEncoder,
    probability: np.ndarray,
    symbols: np.ndarray,
    trace: array,
) -> None:
    cumulative = np.cumsum(probability, axis=1, dtype=np.float64)
    for row, symbol_value in enumerate(symbols):
        symbol = int(symbol_value)
        start = 0
        active = probability.shape[1]
        mass = 1.0
        while active > 1:
            left = active >> 1
            p_zero, left_mass = probability_zero(
                cumulative[row], start, left, mass
            )
            bit = int(symbol >= start + left)
            encoder.put_bit(p_zero, bit)
            trace.append(p_zero)
            if bit:
                start += left
                active -= left
                mass -= left_mass
            else:
                active = left
                mass = left_mass


def decode_with_trace(
    payload: bytes, branch_trace: array, symbol_count: int, vocabulary: int
) -> np.ndarray:
    decoder = RangeDecoder(payload)
    output = np.empty(symbol_count, dtype=np.uint16)
    trace_index = 0
    for row in range(symbol_count):
        start = 0
        active = vocabulary
        while active > 1:
            if trace_index >= len(branch_trace):
                raise ValueError("branch trace ended early")
            probability = int(branch_trace[trace_index])
            trace_index += 1
            left = active >> 1
            if decoder.get_bit(probability):
                start += left
                active -= left
            else:
                active = left
        output[row] = start
    if trace_index != len(branch_trace):
        raise ValueError("branch trace has unused probabilities")
    return output


def model_fingerprint(model: nn.Module) -> str:
    digest = hashlib.sha256()
    with torch.no_grad():
        for name, parameter in model.named_parameters():
            digest.update(name.encode())
            flat = parameter.detach().view(-1)
            if flat.numel():
                indices = torch.linspace(
                    0,
                    flat.numel() - 1,
                    steps=min(32, flat.numel()),
                    device=flat.device,
                ).long()
                digest.update(flat[indices].float().cpu().numpy().tobytes())
    return digest.hexdigest()


def causal_audit(
    model: RocmTeacher, config: Config, device: torch.device
) -> float:
    model.eval()
    first = torch.arange(16, device=device)[None, :].remainder(
        config.vocabulary
    )
    second = first.clone()
    second[0, 9] = (second[0, 9] + 17) % config.vocabulary
    with torch.no_grad(), torch.autocast(
        device_type="cuda", dtype=torch.bfloat16
    ):
        empty = model.empty_memory(device, torch.bfloat16)
        first_logits, _ = model(first, empty)
        empty = model.empty_memory(device, torch.bfloat16)
        second_logits, _ = model(second, empty)
    # The changed input at position 9 may affect prediction 9 and later, but
    # never positions 0 through 8.
    return float(
        (first_logits[:, :9] - second_logits[:, :9]).abs().max().cpu()
    )


def run_teacher(
    symbols: np.ndarray,
    config: Config,
    device: torch.device,
) -> dict[str, object]:
    torch.manual_seed(config.seed)
    torch.cuda.manual_seed_all(config.seed)
    model = RocmTeacher(config).to(device)
    parameter_count = sum(parameter.numel() for parameter in model.parameters())
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=config.learning_rate,
        betas=(config.adam_beta1, config.adam_beta2),
        eps=config.adam_epsilon,
    )
    audit_error = causal_audit(model, config, device)
    model.train()
    memories = model.empty_memory(device, torch.bfloat16)
    previous = np.empty_like(symbols)
    previous[0] = 0
    previous[1:] = symbols[:-1]
    encoder = RangeEncoder()
    trace = array("H")
    loss_sum = 0.0
    started = time.monotonic()
    for start in range(0, len(symbols), config.segment_length):
        end = min(start + config.segment_length, len(symbols))
        input_tensor = torch.from_numpy(
            previous[start:end].astype(np.int64, copy=False)
        )[None, :].to(device)
        target_tensor = torch.from_numpy(
            symbols[start:end].astype(np.int64, copy=False)
        )[None, :].to(device)
        optimizer.zero_grad(set_to_none=True)
        with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
            logits, next_memories = model(input_tensor, memories)
            loss = F.cross_entropy(
                logits.reshape(-1, config.vocabulary),
                target_tensor.reshape(-1),
            )
        probability = torch.softmax(logits.detach(), dim=-1).cpu().numpy()
        encode_distribution(
            encoder, probability, symbols[start:end], trace
        )
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            model.parameters(), config.gradient_clip
        )
        optimizer.step()
        memories = next_memories
        loss_sum += float(loss.detach().cpu()) * (end - start)
    payload = encoder.finish()
    torch.cuda.synchronize(device)
    return {
        "archive": payload,
        "branch_trace": trace,
        "causal_audit_maximum_error": audit_error,
        "elapsed_seconds": time.monotonic() - started,
        "final_model_fingerprint": model_fingerprint(model),
        "mean_cross_entropy_nats": loss_sum / len(symbols),
        "parameter_count": parameter_count,
        "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
        "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
    }


def write_trace(path: Path, trace: array, symbols: int) -> None:
    if struct.pack("=H", 1) != struct.pack("<H", 1):
        trace.byteswap()
    with path.open("wb") as output:
        output.write(TRACE_MAGIC)
        output.write(struct.pack("<QQ", symbols, len(trace)))
        trace.tofile(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preprocessed", required=True, type=Path)
    parser.add_argument("--symbol-map", required=True, type=Path)
    parser.add_argument("--dictionary", required=True, type=Path)
    parser.add_argument("--raw-input", required=True, type=Path)
    parser.add_argument("--nncp-binary", required=True, type=Path)
    parser.add_argument("--symbols", type=int, default=65536)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    if not torch.cuda.is_available() or torch.version.hip is None:
        raise SystemExit("a PyTorch ROCm device is required")
    if args.symbols != 65536:
        raise ValueError("Q0 is frozen at exactly 65,536 symbols")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    config = Config()
    source = np.memmap(args.preprocessed, mode="r", dtype=">u2")
    symbols = np.asarray(source[: args.symbols], dtype=np.uint16)
    if int(symbols.max()) >= config.vocabulary:
        raise ValueError("symbol exceeds frozen vocabulary")

    torch.use_deterministic_algorithms(True)
    device = torch.device("cuda")
    torch.cuda.reset_peak_memory_stats(device)
    trace_off = run_teacher(symbols, config, device)
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(device)
    trace_on = run_teacher(symbols, config, device)
    if trace_off["archive"] != trace_on["archive"]:
        raise ValueError("teacher archive is nondeterministic")
    if (
        trace_off["final_model_fingerprint"]
        != trace_on["final_model_fingerprint"]
    ):
        raise ValueError("teacher final model fingerprint is nondeterministic")
    if trace_on["causal_audit_maximum_error"] != 0:
        raise ValueError("causal mask audit failed")

    payload = trace_on["archive"]
    branch_trace = trace_on["branch_trace"]
    decoded = decode_with_trace(
        payload, branch_trace, args.symbols, config.vocabulary
    )
    if not np.array_equal(decoded, symbols):
        raise ValueError("trace-driven arithmetic reconstruction failed")

    archive_path = args.output_dir / "teacher_payload.bin"
    archive_path.write_bytes(payload)
    trace_path = args.output_dir / "teacher_branch_trace.bin"
    write_trace(trace_path, branch_trace, args.symbols)
    decoded_symbols = args.output_dir / "decoded_symbols.bin"
    decoded.astype(">u2").tofile(decoded_symbols)

    map_dtype = np.dtype(
        [("raw_start", "<u8"), ("raw_end", "<u8"), ("symbol", "<u2")]
    )
    mapped = np.memmap(
        args.symbol_map,
        mode="r",
        dtype=map_dtype,
        offset=16,
        shape=(args.symbols,),
    )
    raw_bytes = int(mapped["raw_end"][-1])
    restored = args.output_dir / "restored.raw"
    environment = os.environ.copy()
    environment["LD_LIBRARY_PATH"] = str(args.nncp_binary.parent)
    subprocess.run(
        [
            str(args.nncp_binary),
            "--dict",
            str(args.dictionary),
            "pd",
            str(decoded_symbols),
            str(restored),
        ],
        check=True,
        env=environment,
    )
    expected = args.raw_input.open("rb").read(raw_bytes)
    if restored.read_bytes() != expected:
        raise ValueError("official inverse differs from raw prefix")

    script = Path(__file__).resolve()
    receipt = {
        "archive": {
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        },
        "branch_trace": {
            "branches": len(branch_trace),
            "bytes": trace_path.stat().st_size,
            "sha256": sha256(trace_path),
        },
        "causality": {
            "maximum_prefix_error": trace_on[
                "causal_audit_maximum_error"
            ],
            "shifted_inputs_only": True,
        },
        "claims": {
            "libnc_parity": False,
            "model_decoder_constructive": False,
            "rocm_teacher_codelength_exact": True,
            "score_credit": False,
            "trace_driven_arithmetic_roundtrip": True,
        },
        "config": asdict(config),
        "deterministic_second_archive": True,
        "environment": {
            "device": torch.cuda.get_device_name(device),
            "hip": torch.version.hip,
            "python": platform.python_version(),
            "script_sha256": sha256(script),
            "torch": torch.__version__,
        },
        "input": {
            "dictionary_sha256": sha256(args.dictionary),
            "preprocessed_sha256": sha256(args.preprocessed),
            "raw_prefix_bytes": raw_bytes,
            "raw_prefix_sha256": hashlib.sha256(expected).hexdigest(),
            "symbols": args.symbols,
        },
        "model": {
            "final_fingerprint": trace_on["final_model_fingerprint"],
            "mean_cross_entropy_nats": trace_on[
                "mean_cross_entropy_nats"
            ],
            "parameters": trace_on["parameter_count"],
        },
        "resource": {
            "peak_allocated_bytes": max(
                trace_off["peak_allocated_bytes"],
                trace_on["peak_allocated_bytes"],
            ),
            "peak_reserved_bytes": max(
                trace_off["peak_reserved_bytes"],
                trace_on["peak_reserved_bytes"],
            ),
            "trace_off_elapsed_seconds": trace_off["elapsed_seconds"],
            "trace_on_elapsed_seconds": trace_on["elapsed_seconds"],
        },
        "roundtrip": {
            "official_raw_inverse": True,
            "symbol_identity": True,
        },
        "schema": "nncp_rocm_q0_teacher_gate_v1",
        "score_credit_bytes": 0,
        "status": "PASS",
    }
    decision = args.output_dir / "decision.json"
    decision.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
