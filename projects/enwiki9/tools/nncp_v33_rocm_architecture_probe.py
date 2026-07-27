#!/usr/bin/env python3
"""Bounded NNCP v3.3 ROCm architecture/allocation probe.

This is not a compressor and cannot receive score credit. It instantiates the
fixed v3.3 parameter topology and exercises shape-compatible BF16 attention
and feed-forward kernels. The synthetic relative-position kernel does not
claim parity with LibNC's padding and rel_shift implementation.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass(frozen=True)
class Config:
    vocab_size: int = 413
    layers: int = 20
    d_model: int = 1024
    heads: int = 8
    d_key: int = 128
    d_value: int = 128
    d_inner: int = 3072
    d_pos: int = 320
    segment_length: int = 64
    memory_length: int = 256
    batch_size: int = 1
    dropout: float = 0.19
    attention_dropout: float = 0.19
    tied_embedding: bool = False
    tied_relative_projection: bool = False
    tied_relative_bias: bool = True
    pre_rmsnorm: bool = True
    final_rmsnorm: bool = True
    geglu: bool = True
    query_bias: bool = False
    rotary_position_embedding: bool = False


class RMSNorm(nn.Module):
    def __init__(self, width: int, *, device: torch.device, dtype: torch.dtype):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(width, device=device, dtype=dtype))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        scale = torch.rsqrt(x.float().square().mean(dim=-1, keepdim=True) + 1e-8)
        return (x * scale.to(x.dtype)) * self.weight


class RelativeBlock(nn.Module):
    def __init__(self, cfg: Config, *, device: torch.device, dtype: torch.dtype):
        super().__init__()
        hd_k = cfg.heads * cfg.d_key
        hd_v = cfg.heads * cfg.d_value
        factory = {"device": device, "dtype": dtype}
        self.cfg = cfg
        self.attn_norm = RMSNorm(cfg.d_model, **factory)
        self.ff_norm = RMSNorm(cfg.d_model, **factory)
        self.w_q = nn.Parameter(torch.empty(hd_k, cfg.d_model, **factory))
        self.w_kv = nn.Parameter(
            torch.empty(hd_k + hd_v, cfg.d_model, **factory)
        )
        self.w_o = nn.Parameter(torch.empty(cfg.d_model, hd_v, **factory))
        self.w_r = nn.Parameter(
            torch.empty(cfg.heads, cfg.d_key, cfg.d_pos, **factory)
        )
        self.ff1_weight = nn.Parameter(
            torch.empty(2 * cfg.d_inner, cfg.d_model, **factory)
        )
        self.ff1_bias = nn.Parameter(torch.zeros(2 * cfg.d_inner, **factory))
        self.ff2_weight = nn.Parameter(
            torch.empty(cfg.d_model, cfg.d_inner, **factory)
        )
        self.ff2_bias = nn.Parameter(torch.zeros(cfg.d_model, **factory))
        for parameter in (
            self.w_q,
            self.w_kv,
            self.w_o,
            self.w_r,
            self.ff1_weight,
            self.ff2_weight,
        ):
            nn.init.uniform_(parameter, -0.01, 0.01)

    def forward(
        self,
        x: torch.Tensor,
        memory: torch.Tensor,
        shared_relative_bias: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        cfg = self.cfg
        batch, length, _ = x.shape
        keys_length = cfg.memory_length + length
        normalized = self.attn_norm(x)
        history = torch.cat((memory, normalized), dim=1)
        query = F.linear(normalized, self.w_q)
        key_value = F.linear(history, self.w_kv)
        key, value = torch.split(
            key_value,
            (cfg.heads * cfg.d_key, cfg.heads * cfg.d_value),
            dim=-1,
        )
        query = query.view(batch, length, cfg.heads, cfg.d_key).transpose(1, 2)
        key = key.view(batch, keys_length, cfg.heads, cfg.d_key).transpose(1, 2)
        value = value.view(
            batch, keys_length, cfg.heads, cfg.d_value
        ).transpose(1, 2)

        content_score = torch.einsum("bhtd,bhkd->bhtk", query, key)
        relative_key = self.w_r.transpose(1, 2)
        relative_score = torch.einsum("bhtd,hkd->bhtk", query, relative_key)
        score = (
            content_score
            + relative_score
            + shared_relative_bias[:keys_length].T[None, :, None, :]
        ) / math.sqrt(cfg.d_key)
        query_position = torch.arange(length, device=x.device)[:, None]
        key_position = torch.arange(keys_length, device=x.device)[None, :]
        allowed = key_position <= cfg.memory_length + query_position
        score = score.masked_fill(~allowed[None, None, :, :], -1e30)
        probability = torch.softmax(score.float(), dim=-1).to(x.dtype)
        attended = torch.einsum("bhtk,bhkd->bhtd", probability, value)
        attended = attended.transpose(1, 2).reshape(
            batch, length, cfg.heads * cfg.d_value
        )
        x = x + F.linear(attended, self.w_o)

        ff_input = self.ff_norm(x)
        gate, value_ff = F.linear(
            ff_input, self.ff1_weight, self.ff1_bias
        ).chunk(2, dim=-1)
        hidden = F.gelu(gate) * value_ff
        x = x + F.linear(hidden, self.ff2_weight, self.ff2_bias)
        next_memory = history[:, -cfg.memory_length :, :].detach()
        return x, next_memory


class ArchitectureProbe(nn.Module):
    def __init__(self, cfg: Config, *, device: torch.device, dtype: torch.dtype):
        super().__init__()
        factory = {"device": device, "dtype": dtype}
        self.cfg = cfg
        self.input_embedding = nn.Embedding(cfg.vocab_size, cfg.d_model, **factory)
        self.output_embedding = nn.Parameter(
            torch.empty(cfg.vocab_size, cfg.d_model, **factory)
        )
        self.output_bias = nn.Parameter(torch.zeros(cfg.vocab_size, **factory))
        self.shared_relative_bias = nn.Parameter(
            torch.zeros(cfg.memory_length + cfg.segment_length, cfg.heads, **factory)
        )
        self.blocks = nn.ModuleList(
            RelativeBlock(cfg, device=device, dtype=dtype)
            for _ in range(cfg.layers)
        )
        self.final_norm = RMSNorm(cfg.d_model, **factory)
        nn.init.uniform_(self.input_embedding.weight, -0.01, 0.01)
        nn.init.uniform_(self.output_embedding, -0.01, 0.01)

    def forward(self, token: torch.Tensor) -> torch.Tensor:
        cfg = self.cfg
        x = self.input_embedding(token) * math.sqrt(cfg.d_model)
        memory = [
            torch.zeros(
                cfg.batch_size,
                cfg.memory_length,
                cfg.d_model,
                device=x.device,
                dtype=x.dtype,
            )
            for _ in range(cfg.layers)
        ]
        for index, block in enumerate(self.blocks):
            x, memory[index] = block(
                x,
                memory[index],
                self.shared_relative_bias,
            )
        x = self.final_norm(x)
        return F.linear(x, self.output_embedding, self.output_bias)


def parameter_groups(model: nn.Module) -> dict[str, int]:
    groups: dict[str, int] = {}
    for name, parameter in model.named_parameters():
        prefix = name.split(".", 1)[0]
        groups[prefix] = groups.get(prefix, 0) + parameter.numel()
    return groups


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--vocab-size", type=int, default=413)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--seed", type=int, default=1)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("ROCm/CUDA device is unavailable")
    torch.manual_seed(args.seed)
    torch.use_deterministic_algorithms(True)
    device = torch.device(args.device)
    dtype = torch.bfloat16
    cfg = Config(vocab_size=args.vocab_size)
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
    started = time.monotonic()
    with torch.no_grad():
        model = ArchitectureProbe(cfg, device=device, dtype=dtype)
        token = torch.arange(
            cfg.segment_length, device=device, dtype=torch.long
        )[None, :].remainder(cfg.vocab_size)
        logits = model(token)
        checksum = float(logits.float().sum().cpu())
        if device.type == "cuda":
            torch.cuda.synchronize(device)
    elapsed = time.monotonic() - started
    parameters = sum(parameter.numel() for parameter in model.parameters())
    result = {
        "schema": "gamma.nncp_v33_rocm_architecture_probe.v1",
        "status": "ARCHITECTURE_PROBE_ONLY",
        "score_credit_bytes": 0,
        "config": asdict(cfg),
        "environment": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "hip": torch.version.hip,
            "device": str(device),
            "device_name": (
                torch.cuda.get_device_name(device)
                if device.type == "cuda"
                else platform.processor()
            ),
        },
        "parameter_count": parameters,
        "parameter_bytes_bf16": parameters * 2,
        "parameter_groups": parameter_groups(model),
        "kernel_probe": {
            "output_shape": list(logits.shape),
            "finite": bool(torch.isfinite(logits).all().cpu()),
            "checksum_diagnostic_only": checksum,
            "elapsed_seconds": elapsed,
            "peak_allocated_bytes": (
                torch.cuda.max_memory_allocated(device)
                if device.type == "cuda"
                else None
            ),
            "peak_reserved_bytes": (
                torch.cuda.max_memory_reserved(device)
                if device.type == "cuda"
                else None
            ),
        },
        "claims": {
            "parameter_topology_instantiated": True,
            "bf16_kernel_path_exercised": True,
            "libnc_distribution_parity": False,
            "relative_shift_parity": False,
            "codec_roundtrip": False,
            "compression_improvement": False,
        },
        "next_gate": (
            "Implement LibNC-exact relative feature generation, padding, and "
            "rel_shift; compare frozen CPU-teacher logits before tracing."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
