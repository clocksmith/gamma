#!/usr/bin/env python3
"""Constructive one-update NNCP v3.3 profile gate on PyTorch/ROCm."""

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


ROOT = Path(__file__).resolve().parents[1]
ROCM_PYTHON = Path(
    "/home/x/enwiki9-nonproof/external/rocm-pytorch-venv/bin/python"
)
os.environ.setdefault("AMD_SERIALIZE_KERNEL", "3")
if Path(sys.executable) != ROCM_PYTHON:
    if not ROCM_PYTHON.is_file():
        raise SystemExit(f"missing receipt-bound ROCm interpreter: {ROCM_PYTHON}")
    os.execve(
        str(ROCM_PYTHON),
        [str(ROCM_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
        os.environ.copy(),
    )

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

import nncp_rocm_q0_teacher_gate as coder


TRACE_MAGIC = b"NV3Q0TR1"


@dataclass(frozen=True)
class Config:
    vocabulary: int = 16392
    layers: int = 20
    width: int = 1024
    heads: int = 8
    key_width: int = 128
    value_width: int = 128
    inner_width: int = 3072
    relative_positions: int = 320
    segment_length: int = 64
    memory_length: int = 256
    streams: int = 32
    init_range: float = 0.79
    learning_rate: float = 0.00016
    adam_beta1: float = 0.0
    adam_beta2: float = 0.9999
    adam_epsilon: float = 1e-8
    gradient_clip: float = 0.05
    normalization_epsilon: float = 1e-5
    seed: int = 123


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def libnc_gelu(value: torch.Tensor) -> torch.Tensor:
    half = torch.tensor(0.5, dtype=value.dtype, device=value.device)
    one = torch.tensor(1.0, dtype=value.dtype, device=value.device)
    cubic = torch.tensor(0.044715, dtype=value.dtype, device=value.device)
    scale = torch.sqrt(
        torch.tensor(2.0 / math.pi, dtype=value.dtype, device=value.device)
    )
    argument = scale * (value + cubic * value * value * value)
    tanh_value = torch.tanh(argument)
    tanh_value = torch.where(
        argument >= torch.tensor(8.0, dtype=value.dtype, device=value.device),
        one,
        tanh_value,
    )
    return half * value * (one + tanh_value)


def relative_shift(value: torch.Tensor) -> torch.Tensor:
    batch, heads, query, key = value.shape
    padded = torch.cat((torch.zeros_like(value[..., :1]), value), dim=-1)
    padded = padded.reshape(batch, heads, key + 1, query)
    return padded[:, :, 1:, :].reshape(batch, heads, query, key)


class RMSNormAffine(nn.Module):
    def __init__(self, config: Config) -> None:
        super().__init__()
        factory = {"dtype": torch.bfloat16}
        self.epsilon = config.normalization_epsilon
        self.weight = nn.Parameter(torch.ones(config.width, **factory))
        self.bias = nn.Parameter(torch.zeros(config.width, **factory))

    def forward(self, value: torch.Tensor) -> torch.Tensor:
        scale = torch.rsqrt(
            value.float().square().mean(dim=-1, keepdim=True) + self.epsilon
        )
        normalized = value * scale.to(value.dtype)
        return normalized * self.weight + self.bias


class RelativeBlock(nn.Module):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
        factory = {"dtype": torch.bfloat16}
        key_total = config.heads * config.key_width
        value_total = config.heads * config.value_width
        self.attention_norm = RMSNormAffine(config)
        self.feedforward_norm = RMSNormAffine(config)
        self.query = nn.Parameter(torch.empty(key_total, config.width, **factory))
        self.key_value = nn.Parameter(
            torch.empty(key_total + value_total, config.width, **factory)
        )
        self.output = nn.Parameter(
            torch.empty(config.width, value_total, **factory)
        )
        self.relative = nn.Parameter(
            torch.empty(
                config.heads,
                config.key_width,
                config.relative_positions,
                **factory,
            )
        )
        self.feedforward_in = nn.Parameter(
            torch.empty(2 * config.inner_width, config.width, **factory)
        )
        self.feedforward_in_bias = nn.Parameter(
            torch.zeros(2 * config.inner_width, **factory)
        )
        self.feedforward_out = nn.Parameter(
            torch.empty(config.width, config.inner_width, **factory)
        )
        self.feedforward_out_bias = nn.Parameter(
            torch.zeros(config.width, **factory)
        )

    def reset_parameters(self, bound: float) -> None:
        for parameter in (
            self.query,
            self.key_value,
            self.output,
            self.relative,
            self.feedforward_in,
        ):
            nn.init.uniform_(parameter, -bound, bound)
        nn.init.uniform_(
            self.feedforward_out,
            -bound * math.sqrt(self.config.width / self.config.inner_width),
            bound * math.sqrt(self.config.width / self.config.inner_width),
        )
        nn.init.zeros_(self.feedforward_in_bias)
        nn.init.zeros_(self.feedforward_out_bias)
        nn.init.ones_(self.attention_norm.weight)
        nn.init.zeros_(self.attention_norm.bias)
        nn.init.ones_(self.feedforward_norm.weight)
        nn.init.zeros_(self.feedforward_norm.bias)

    def forward(
        self,
        value: torch.Tensor,
        memory: torch.Tensor,
        shared_relative_bias: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        config = self.config
        batch, length, _ = value.shape
        normalized = self.attention_norm(value)
        history = torch.cat((memory, normalized), dim=1)
        keys_length = history.shape[1]
        if keys_length != config.relative_positions:
            raise ValueError("Q0 requires memory plus segment equal d_pos")

        query = F.linear(normalized, self.query)
        key_value = F.linear(history, self.key_value)
        key, projected_value = torch.split(
            key_value,
            (
                config.heads * config.key_width,
                config.heads * config.value_width,
            ),
            dim=-1,
        )
        query = query.view(
            batch, length, config.heads, config.key_width
        ).transpose(1, 2)
        key = key.view(
            batch, keys_length, config.heads, config.key_width
        ).transpose(1, 2)
        projected_value = projected_value.view(
            batch, keys_length, config.heads, config.value_width
        ).transpose(1, 2)

        content = torch.einsum("bhtd,bhkd->bhtk", query, key)
        relative_key = self.relative.transpose(1, 2)
        relative = torch.einsum("bhtd,hkd->bhtk", query, relative_key)
        relative = relative + shared_relative_bias.T[
            None, :, None, :
        ] * math.sqrt(config.key_width * config.width)
        score = (content + relative_shift(relative)) / math.sqrt(
            config.key_width
        )
        query_position = torch.arange(length, device=value.device)[:, None]
        key_position = torch.arange(keys_length, device=value.device)[None, :]
        allowed = key_position <= config.memory_length + query_position
        score = score.masked_fill(~allowed[None, None, :, :], -torch.inf)
        attention = torch.softmax(score.float(), dim=-1).to(value.dtype)
        attended = torch.einsum(
            "bhtk,bhkd->bhtd", attention, projected_value
        )
        attended = attended.transpose(1, 2).reshape(
            batch, length, config.heads * config.value_width
        )
        value = value + F.linear(attended, self.output)

        feedforward = self.feedforward_norm(value)
        gate, content_ff = F.linear(
            feedforward, self.feedforward_in, self.feedforward_in_bias
        ).chunk(2, dim=-1)
        hidden = libnc_gelu(gate) * content_ff
        value = value + F.linear(
            hidden, self.feedforward_out, self.feedforward_out_bias
        )
        return value, history[:, -config.memory_length :, :]


class FaithfulModel(nn.Module):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
        self.embedding = nn.Parameter(
            torch.empty(config.vocabulary, config.width, dtype=torch.float32)
        )
        self.blocks = nn.ModuleList(
            RelativeBlock(config) for _ in range(config.layers)
        )
        self.final_norm = RMSNormAffine(config)
        self.output_embedding = nn.Parameter(
            torch.empty(
                config.vocabulary, config.width, dtype=torch.bfloat16
            )
        )
        self.output_bias = nn.Parameter(
            torch.zeros(config.vocabulary, dtype=torch.bfloat16)
        )
        self.shared_relative_bias = nn.Parameter(
            torch.zeros(
                config.relative_positions,
                config.heads,
                dtype=torch.bfloat16,
            )
        )
        self.reset_parameters()

    def reset_parameters(self) -> None:
        bound = self.config.init_range / math.sqrt(self.config.width)
        nn.init.uniform_(self.embedding, -bound, bound)
        nn.init.uniform_(self.output_embedding, -bound, bound)
        nn.init.zeros_(self.output_bias)
        nn.init.zeros_(self.shared_relative_bias)
        nn.init.ones_(self.final_norm.weight)
        nn.init.zeros_(self.final_norm.bias)
        for block in self.blocks:
            block.reset_parameters(bound)

    def empty_memory(self, device: torch.device) -> list[torch.Tensor]:
        config = self.config
        return [
            torch.zeros(
                config.streams,
                config.memory_length,
                config.width,
                dtype=torch.bfloat16,
                device=device,
            )
            for _ in self.blocks
        ]

    def forward(
        self, symbols: torch.Tensor, memories: list[torch.Tensor]
    ) -> tuple[torch.Tensor, list[torch.Tensor]]:
        config = self.config
        value = F.embedding(symbols, self.embedding).to(torch.bfloat16)
        value = value * math.sqrt(config.width)
        next_memories: list[torch.Tensor] = []
        for block, memory in zip(self.blocks, memories, strict=True):
            value, next_memory = block(
                value, memory, self.shared_relative_bias
            )
            next_memories.append(next_memory)
        value = self.final_norm(value)
        logits = F.linear(value, self.output_embedding, self.output_bias).float()
        return logits, next_memories


def parameter_state_hash(model: nn.Module) -> str:
    digest = hashlib.sha256()
    with torch.no_grad():
        for name, parameter in model.named_parameters():
            value = parameter.detach().contiguous().cpu()
            digest.update(name.encode("utf-8") + b"\0")
            digest.update(str(value.dtype).encode("ascii") + b"\0")
            digest.update(struct.pack("<I", value.ndim))
            for dimension in value.shape:
                digest.update(struct.pack("<Q", dimension))
            if value.dtype == torch.bfloat16:
                digest.update(value.view(torch.uint16).numpy().tobytes())
            else:
                digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def per_parameter_clip(model: nn.Module, limit: float) -> None:
    for parameter in model.parameters():
        if parameter.grad is None:
            continue
        norm = torch.linalg.vector_norm(parameter.grad.float())
        if bool(norm > limit):
            parameter.grad.mul_((limit / norm).to(parameter.grad.dtype))


def make_model(config: Config, device: torch.device) -> FaithfulModel:
    torch.manual_seed(config.seed)
    torch.cuda.manual_seed_all(config.seed)
    return FaithfulModel(config).to(device)


def model_contract(config: Config, model: nn.Module) -> dict[str, int]:
    count = sum(parameter.numel() for parameter in model.parameters())
    bytes_ = sum(
        parameter.numel() * parameter.element_size()
        for parameter in model.parameters()
    )
    return {"parameter_count": count, "parameter_bytes": bytes_}


def shifted_inputs(targets: torch.Tensor) -> torch.Tensor:
    inputs = torch.zeros_like(targets)
    inputs[:, 1:] = targets[:, :-1]
    return inputs


def optimizer_for(model: nn.Module, config: Config) -> torch.optim.Optimizer:
    return torch.optim.Adam(
        model.parameters(),
        lr=config.learning_rate,
        betas=(config.adam_beta1, config.adam_beta2),
        eps=config.adam_epsilon,
        weight_decay=0.0,
    )


def branch_encode(
    encoder: coder.RangeEncoder,
    probability: np.ndarray,
    target: np.ndarray,
    trace: array,
) -> None:
    coder.encode_distribution(encoder, probability, target, trace)


def branch_decode_one(
    decoder: coder.RangeDecoder, probability: np.ndarray, trace: array
) -> int:
    cumulative = np.cumsum(probability, dtype=np.float64)
    start = 0
    active = len(probability)
    mass = 1.0
    while active > 1:
        left = active >> 1
        probability_zero, left_mass = coder.probability_zero(
            cumulative, start, left, mass
        )
        trace.append(probability_zero)
        if decoder.get_bit(probability_zero):
            start += left
            active -= left
            mass -= left_mass
        else:
            active = left
            mass = left_mass
    return start


def update_model(
    model: FaithfulModel,
    optimizer: torch.optim.Optimizer,
    logits: torch.Tensor,
    targets: torch.Tensor,
    config: Config,
) -> float:
    loss = F.cross_entropy(
        logits.reshape(-1, config.vocabulary), targets.reshape(-1)
    )
    loss.backward()
    per_parameter_clip(model, config.gradient_clip)
    optimizer.step()
    return float(loss.detach().cpu())


def encode_once(
    symbols: np.ndarray, config: Config, device: torch.device, label: str
) -> dict[str, object]:
    print(json.dumps({"event": "encode_start", "label": label}), flush=True)
    torch.cuda.reset_peak_memory_stats(device)
    model = make_model(config, device)
    contract = model_contract(config, model)
    optimizer = optimizer_for(model, config)
    target_numpy = symbols.reshape(config.streams, config.segment_length)
    targets = torch.from_numpy(target_numpy.astype(np.int64)).to(device)
    inputs = shifted_inputs(targets)
    memories = model.empty_memory(device)
    optimizer.zero_grad(set_to_none=True)
    started = time.monotonic()
    logits, _ = model(inputs, memories)
    probability = torch.softmax(logits.detach(), dim=-1).cpu().numpy()
    encoder = coder.RangeEncoder()
    trace = array("H")
    for state in range(config.segment_length):
        branch_encode(
            encoder,
            probability[:, state, :],
            target_numpy[:, state],
            trace,
        )
    payload = encoder.finish()
    loss = update_model(model, optimizer, logits, targets, config)
    torch.cuda.synchronize(device)
    result = {
        "archive": payload,
        "branch_trace": trace,
        "elapsed_seconds": time.monotonic() - started,
        "final_state_sha256": parameter_state_hash(model),
        "loss_nats": loss,
        "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
        "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
        **contract,
    }
    del optimizer, model, logits, probability, targets, inputs, memories
    torch.cuda.empty_cache()
    print(
        json.dumps(
            {
                "archive_bytes": len(payload),
                "event": "encode_complete",
                "label": label,
                "state_sha256": result["final_state_sha256"],
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return result


def decode_once(
    payload: bytes, config: Config, device: torch.device
) -> dict[str, object]:
    print(json.dumps({"event": "decode_start"}), flush=True)
    torch.cuda.reset_peak_memory_stats(device)
    model = make_model(config, device)
    optimizer = optimizer_for(model, config)
    memories = model.empty_memory(device)
    decoded = torch.zeros(
        config.streams,
        config.segment_length,
        dtype=torch.long,
        device=device,
    )
    inputs = torch.zeros_like(decoded)
    decoder = coder.RangeDecoder(payload)
    trace = array("H")
    final_logits = None
    started = time.monotonic()
    for state in range(config.segment_length):
        if state:
            inputs[:, state] = decoded[:, state - 1]
        if state + 1 == config.segment_length:
            optimizer.zero_grad(set_to_none=True)
            logits, _ = model(inputs, memories)
            final_logits = logits
        else:
            with torch.no_grad():
                logits, _ = model(inputs, memories)
        probability = torch.softmax(
            logits[:, state, :].detach(), dim=-1
        ).cpu().numpy()
        for stream in range(config.streams):
            decoded[stream, state] = branch_decode_one(
                decoder, probability[stream], trace
            )
        if (state + 1) % 8 == 0:
            print(
                json.dumps(
                    {
                        "event": "decode_checkpoint",
                        "states": state + 1,
                        "total_states": config.segment_length,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
    if final_logits is None:
        raise AssertionError("missing final differentiable logits")
    loss = update_model(model, optimizer, final_logits, decoded, config)
    torch.cuda.synchronize(device)
    result = {
        "branch_trace": trace,
        "decoded": decoded.detach().cpu().numpy().astype(np.uint16),
        "elapsed_seconds": time.monotonic() - started,
        "final_state_sha256": parameter_state_hash(model),
        "loss_nats": loss,
        "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
        "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
    }
    del optimizer, model, final_logits, decoded, inputs, memories
    torch.cuda.empty_cache()
    print(
        json.dumps(
            {
                "event": "decode_complete",
                "state_sha256": result["final_state_sha256"],
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return result


def causal_audit(config: Config, device: torch.device) -> float:
    model = make_model(config, device)
    memories = model.empty_memory(device)
    first = torch.arange(
        config.streams * config.segment_length, device=device
    ).reshape(config.streams, config.segment_length) % config.vocabulary
    second = first.clone()
    second[:, 9] = (second[:, 9] + 17) % config.vocabulary
    with torch.no_grad():
        first_logits, _ = model(first, memories)
        second_logits, _ = model(second, memories)
    error = float(
        (first_logits[:, :9] - second_logits[:, :9]).abs().max().cpu()
    )
    del model, memories, first, second, first_logits, second_logits
    torch.cuda.empty_cache()
    return error


def trace_bytes(trace: array) -> bytes:
    copy = array("H", trace)
    if struct.pack("=H", 1) != struct.pack("<H", 1):
        copy.byteswap()
    return copy.tobytes()


def matrix_probe(device: torch.device) -> str:
    left = torch.arange(4096, dtype=torch.float32, device=device).reshape(64, 64)
    right = torch.flip(left, dims=(0,))
    output = left @ right
    torch.cuda.synchronize(device)
    return hashlib.sha256(output.cpu().numpy().tobytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preprocessed",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/"
            "preprocessed.bin"
        ),
    )
    parser.add_argument(
        "--symbol-map",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/"
            "symbol_raw_map.bin"
        ),
    )
    parser.add_argument(
        "--dictionary",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/"
            "dictionary.bin"
        ),
    )
    parser.add_argument(
        "--raw-input", type=Path, default=ROOT / "data/enwik9_1000000.bin"
    )
    parser.add_argument(
        "--nncp-binary",
        type=Path,
        default=Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05/nncp"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "results/nncp_v33_rocm_constructive_one_update_q0_v1",
    )
    args = parser.parse_args()
    required = (
        args.preprocessed,
        args.symbol_map,
        args.dictionary,
        args.raw_input,
        args.nncp_binary,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit(f"missing inputs: {missing}")
    if not torch.cuda.is_available() or torch.version.hip is None:
        raise SystemExit("PyTorch ROCm is required")

    config = Config()
    torch.use_deterministic_algorithms(True)
    device = torch.device("cuda")
    matrix_sha256 = matrix_probe(device)
    runtime = {
        "sys_executable": sys.executable,
        "python": platform.python_version(),
        "torch": torch.__version__,
        "hip": torch.version.hip,
        "device": torch.cuda.get_device_name(device),
        "device_count": torch.cuda.device_count(),
        "matrix_output_sha256": matrix_sha256,
        "runtime_mode": (
            "rocm_gfx_override"
            if os.environ.get("HSA_OVERRIDE_GFX_VERSION")
            else "normal_rocm"
        ),
    }
    print(json.dumps({"event": "runtime_preflight", **runtime}), flush=True)

    source = np.memmap(args.preprocessed, mode="r", dtype=">u2")
    symbol_count = config.streams * config.segment_length
    symbols = np.asarray(source[:symbol_count], dtype=np.uint16)
    if int(symbols.max()) >= config.vocabulary:
        raise ValueError("symbol exceeds profile vocabulary")

    audit_error = causal_audit(config, device)
    print(
        json.dumps(
            {"event": "causal_audit", "maximum_prefix_error": audit_error}
        ),
        flush=True,
    )
    if audit_error != 0.0:
        raise ValueError("future perturbation changed causal prefix")

    first = encode_once(symbols, config, device, "first")
    second = encode_once(symbols, config, device, "second")
    decoded = decode_once(first["archive"], config, device)
    encoder_trace = trace_bytes(first["branch_trace"])
    second_trace = trace_bytes(second["branch_trace"])
    decoder_trace = trace_bytes(decoded["branch_trace"])
    decoded_linear = decoded["decoded"].reshape(-1)

    archive_repeat = first["archive"] == second["archive"]
    frequency_identity = encoder_trace == second_trace == decoder_trace
    symbol_identity = np.array_equal(decoded_linear, symbols)
    state_identity = (
        first["final_state_sha256"]
        == second["final_state_sha256"]
        == decoded["final_state_sha256"]
    )
    loss_identity = first["loss_nats"] == second["loss_nats"] == decoded["loss_nats"]
    if not all(
        (archive_repeat, frequency_identity, symbol_identity, state_identity, loss_identity)
    ):
        raise ValueError("constructive encode/decode identity failed")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = args.output_dir / "archive.bin"
    archive_path.write_bytes(first["archive"])
    trace_path = args.output_dir / "branch_trace.bin"
    trace_path.write_bytes(encoder_trace)
    decoded_path = args.output_dir / "decoded_symbols.bin"
    decoded_linear.astype(">u2").tofile(decoded_path)

    map_dtype = np.dtype(
        [("raw_start", "<u8"), ("raw_end", "<u8"), ("symbol", "<u2")]
    )
    mapped = np.memmap(
        args.symbol_map,
        mode="r",
        dtype=map_dtype,
        offset=16,
        shape=(symbol_count,),
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
            str(decoded_path),
            str(restored),
        ],
        check=True,
        env=environment,
        capture_output=True,
    )
    expected_raw = args.raw_input.read_bytes()[:raw_bytes]
    raw_identity = restored.read_bytes() == expected_raw
    if not raw_identity:
        raise ValueError("official inverse differs from raw prefix")

    peak_allocated = max(
        first["peak_allocated_bytes"],
        second["peak_allocated_bytes"],
        decoded["peak_allocated_bytes"],
    )
    memory_pass = peak_allocated < 10_000_000_000
    if not memory_pass:
        raise ValueError("decimal 10 GB allocation gate failed")
    script = Path(__file__).resolve()
    decision = {
        "schema": "gamma.nncp_v33_rocm_constructive_one_update_q0.v1",
        "candidate_id": "nncp_v33_rocm_constructive_one_update_q0_v1",
        "status": "AUTHORIZED_65536_HEADROOM" if memory_pass else "REJECT",
        "score_credit_bytes": 0,
        "claim_boundary": (
            "Self-consistent one-update source-level construction only; no "
            "LibNC parity or published-score inheritance."
        ),
        "config": asdict(config),
        "runtime": runtime,
        "inputs": {
            "preprocessed": {
                "path": str(args.preprocessed),
                "sha256": sha256(args.preprocessed),
            },
            "symbol_map": {
                "path": str(args.symbol_map),
                "sha256": sha256(args.symbol_map),
            },
            "dictionary": {
                "path": str(args.dictionary),
                "sha256": sha256(args.dictionary),
            },
            "raw_input": {
                "path": str(args.raw_input),
                "sha256": sha256(args.raw_input),
            },
            "nncp_binary": {
                "path": str(args.nncp_binary),
                "sha256": sha256(args.nncp_binary),
            },
            "script_sha256": sha256(script),
        },
        "population": {
            "symbols": symbol_count,
            "raw_bytes": raw_bytes,
            "streams": config.streams,
            "symbols_per_stream": config.segment_length,
        },
        "model": {
            "parameter_count": first["parameter_count"],
            "parameter_bytes": first["parameter_bytes"],
            "final_state_sha256": first["final_state_sha256"],
            "loss_nats": first["loss_nats"],
        },
        "archive": {
            "bytes": len(first["archive"]),
            "sha256": hashlib.sha256(first["archive"]).hexdigest(),
            "branch_frequencies": len(first["branch_trace"]),
            "branch_trace_sha256": hashlib.sha256(encoder_trace).hexdigest(),
        },
        "integrity": {
            "archive_repeat_byte_identical": archive_repeat,
            "branch_frequency_identity": frequency_identity,
            "causal_future_perturbation_exact": audit_error == 0.0,
            "decoded_symbol_identity": symbol_identity,
            "final_model_state_identity": state_identity,
            "loss_identity": loss_identity,
            "official_raw_inverse": raw_identity,
        },
        "resource": {
            "first_encode_seconds": first["elapsed_seconds"],
            "second_encode_seconds": second["elapsed_seconds"],
            "decode_seconds": decoded["elapsed_seconds"],
            "peak_allocated_bytes": peak_allocated,
            "peak_reserved_bytes": max(
                first["peak_reserved_bytes"],
                second["peak_reserved_bytes"],
                decoded["peak_reserved_bytes"],
            ),
            "decimal_10gb_allocated_pass": memory_pass,
        },
        "decision": {
            "promotion_authorized": memory_pass,
            "authorized_next_action": "run one frozen 65,536-symbol headroom gate",
            "forecast_bytes": 109389323,
            "verified_full_1g_score_bytes": None,
        },
    }
    decision_path = args.output_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
