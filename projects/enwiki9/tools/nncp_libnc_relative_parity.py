#!/usr/bin/env python3
"""Compare a frozen miniature LibNC Transformer with a PyTorch realization."""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F


TRACE_HEADER = struct.Struct("<8sQ")
TRACE_ROW = struct.Struct("<QQQQIHHI")


def load_export(path: Path) -> tuple[dict[str, torch.Tensor], list[str]]:
    manifest = json.loads((path / "manifest.json").read_text())
    tensors: dict[str, torch.Tensor] = {}
    exported_types: set[str] = set()
    for item in manifest["tensors"]:
        exported_types.add(item["type"])
        if item["type"] == "f32":
            values = np.fromfile(path / item["payload"], dtype="<f4")
        elif item["type"] == "bf16":
            words = np.fromfile(path / item["payload"], dtype="<u2")
            values = (words.astype(np.uint32) << 16).view(np.float32)
        else:
            raise ValueError(f"unsupported tensor type: {item['type']}")
        array = values.reshape(item["dims"], order="F").copy()
        tensors[item["name"]] = torch.from_numpy(array)
    if not exported_types:
        raise ValueError("empty tensor export")
    return tensors, sorted(exported_types)


def load_trace(path: Path) -> tuple[np.ndarray, list[np.ndarray]]:
    symbols: list[int] = []
    distributions: list[np.ndarray] = []
    with path.open("rb") as source:
        magic, rows = TRACE_HEADER.unpack(source.read(TRACE_HEADER.size))
        if magic != b"NNTCHD2\0":
            raise ValueError("invalid teacher trace")
        for index in range(rows):
            fixed = TRACE_ROW.unpack(source.read(TRACE_ROW.size))
            if fixed[1] != index:
                raise ValueError("nonconsecutive execution row")
            n_symbols = fixed[-1]
            distribution = np.frombuffer(
                source.read(4 * n_symbols), dtype="<f4"
            ).copy()
            symbols.append(fixed[-2])
            distributions.append(distribution)
        if source.read(1):
            raise ValueError("trailing teacher trace bytes")
    return np.asarray(symbols, dtype=np.int64), distributions


def rms_norm(x: torch.Tensor, gain: torch.Tensor, bias: torch.Tensor) -> torch.Tensor:
    normalized = x * torch.rsqrt(x.square().mean(dim=-1, keepdim=True) + 1e-5)
    return normalized * gain + bias


def relative_shift(x: torch.Tensor) -> torch.Tensor:
    """Transformer-XL relative shift for [head, query, key] tensors."""
    heads, query, key = x.shape
    padded = torch.cat((torch.zeros_like(x[:, :, :1]), x), dim=2)
    padded = padded.reshape(heads, key + 1, query)
    return padded[:, 1:, :].reshape(heads, query, key)


def forward_segment(
    weights: dict[str, torch.Tensor],
    token: torch.Tensor,
    memory: torch.Tensor,
    segment: int,
    memory_length: int,
    heads: int,
    d_key: int,
    d_value: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    d_model = weights["embed"].shape[0]
    layer_input = weights["embed"][:, token].T.contiguous() * d_model**0.5
    normalized = rms_norm(
        layer_input, weights["ln_g_0"], weights["ln_b_0"]
    )
    history = torch.cat((memory, normalized), dim=0)
    query = F.linear(normalized, weights["w_q_0"])
    key_value = F.linear(history, weights["w_kv_0"])
    key, value = torch.split(
        key_value, (heads * d_key, heads * d_value), dim=-1
    )
    query = query.view(segment, heads, d_key).permute(1, 0, 2)
    key = key.view(memory_length + segment, heads, d_key).permute(1, 0, 2)
    value = value.view(
        memory_length + segment, heads, d_value
    ).permute(1, 0, 2)
    content = torch.einsum("hkd,htd->htk", key, query)
    w_r = weights["w_r_0"].permute(2, 1, 0)
    relative = torch.einsum("hkd,htd->htk", w_r, query)
    relative = relative + (
        weights["b_r_0"].T[:, None, :] * (d_key * d_model) ** 0.5
    )
    score = (content + relative_shift(relative)) / d_key**0.5
    device = score.device
    qpos = torch.arange(segment, device=device)[:, None]
    kpos = torch.arange(memory_length + segment, device=device)[None, :]
    mask = kpos > memory_length + qpos
    score = score.masked_fill(mask[None, :, :], -torch.inf)
    probability = torch.softmax(score, dim=-1)
    attended = torch.einsum("htk,hkd->htd", probability, value)
    attended = attended.permute(1, 0, 2).reshape(segment, heads * d_value)
    layer_input = layer_input + F.linear(attended, weights["w_o_0"])
    ff_input = rms_norm(
        layer_input, weights["ln_g_1"], weights["ln_b_1"]
    )
    gate, value_ff = F.linear(
        ff_input, weights["ff1_0"], weights["ff_bias1_0"]
    ).chunk(2, dim=-1)
    hidden = F.gelu(gate) * value_ff
    layer_input = layer_input + F.linear(
        hidden, weights["ff2_0"], weights["ff_bias2_0"]
    )
    layer_input = rms_norm(
        layer_input, weights["ln_g_2"], weights["ln_b_2"]
    )
    logits = F.linear(
        layer_input, weights["embed_out"], weights["out_bias"]
    ).float()
    next_memory = torch.cat((memory, normalized), dim=0)[-memory_length:]
    return logits, next_memory


def evaluate(
    weights: dict[str, torch.Tensor],
    symbols: np.ndarray,
    segment: int,
    memory_length: int,
    heads: int,
    d_key: int,
    d_value: int,
    device: torch.device,
    dtype: torch.dtype,
) -> torch.Tensor:
    weights = {name: value.to(device=device, dtype=dtype) for name, value in weights.items()}
    d_model = weights["embed"].shape[0]
    inputs = np.concatenate((np.zeros(1, dtype=np.int64), symbols[:-1]))
    memory = torch.zeros(memory_length, d_model, device=device, dtype=dtype)
    outputs: list[torch.Tensor] = []
    for start in range(0, len(symbols), segment):
        token = torch.from_numpy(inputs[start : start + segment]).to(device)
        logits, next_memory = forward_segment(
            weights,
            token,
            memory,
            segment,
            memory_length,
            heads,
            d_key,
            d_value,
        )
        outputs.append(torch.softmax(logits, dim=-1).cpu())
        memory = next_memory
    return torch.cat(outputs, dim=0)


def evaluate_online(
    initial: dict[str, torch.Tensor],
    symbols: np.ndarray,
    segment: int,
    memory_length: int,
    heads: int,
    d_key: int,
    d_value: int,
    device: torch.device,
    dtype: torch.dtype,
    learning_rate: float,
    gradient_clip: float,
) -> tuple[torch.Tensor, dict[str, torch.Tensor], list[float]]:
    parameters = {
        name: torch.nn.Parameter(value.to(device=device, dtype=dtype))
        for name, value in initial.items()
    }
    optimizer = torch.optim.Adam(
        list(parameters.values()),
        lr=learning_rate,
        betas=(0.0, 0.9999),
        eps=1e-8,
    )
    d_model = parameters["embed"].shape[0]
    memory = torch.zeros(
        memory_length, d_model, device=device, dtype=dtype
    )
    inputs = np.concatenate((np.zeros(1, dtype=np.int64), symbols[:-1]))
    outputs: list[torch.Tensor] = []
    losses: list[float] = []
    for start in range(0, len(symbols), segment):
        token = torch.from_numpy(inputs[start : start + segment]).to(device)
        target = torch.from_numpy(symbols[start : start + segment]).to(device)
        optimizer.zero_grad(set_to_none=True)
        logits, next_memory = forward_segment(
            parameters,
            token,
            memory,
            segment,
            memory_length,
            heads,
            d_key,
            d_value,
        )
        outputs.append(torch.softmax(logits.detach(), dim=-1).cpu())
        loss = F.cross_entropy(logits, target, reduction="mean")
        losses.append(float(loss.detach().cpu()))
        loss.backward()
        for parameter in parameters.values():
            if parameter.grad is not None:
                parameter.grad.clamp_(-gradient_clip, gradient_clip)
        optimizer.step()
        memory = next_memory.detach()
    final = {
        name: parameter.detach().float().cpu()
        for name, parameter in parameters.items()
    }
    return torch.cat(outputs, dim=0), final, losses


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", type=Path, required=True)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--compute-dtype", choices=("f32", "bf16"), default="f32"
    )
    parser.add_argument("--tolerance", type=float, default=2e-5)
    parser.add_argument("--online-lr", type=float)
    parser.add_argument("--gradient-clip", type=float, default=0.05)
    parser.add_argument("--final-export", type=Path)
    args = parser.parse_args()

    torch.set_default_dtype(torch.float32)
    weights, exported_types = load_export(args.export)
    symbols, distributions = load_trace(args.trace)
    teacher = torch.from_numpy(np.stack(distributions))
    device = torch.device(args.device)
    dtype = torch.float32 if args.compute_dtype == "f32" else torch.bfloat16
    losses: list[float] | None = None
    final_parameter_error: dict[str, float] | None = None
    if args.online_lr is None:
        student = evaluate(weights, symbols, 4, 4, 2, 8, 8, device, dtype)
    else:
        if args.final_export is None:
            raise ValueError("--online-lr requires --final-export")
        student, final, losses = evaluate_online(
            weights,
            symbols,
            4,
            4,
            2,
            8,
            8,
            device,
            dtype,
            args.online_lr,
            args.gradient_clip,
        )
        teacher_final, _ = load_export(args.final_export)
        final_parameter_error = {
            name: float((final[name] - teacher_final[name]).abs().max())
            for name in sorted(final)
        }
    error = (student - teacher).abs()
    max_parameter_error = (
        max(final_parameter_error.values())
        if final_parameter_error is not None
        else 0.0
    )
    passed = (
        float(error.max()) <= args.tolerance
        and max_parameter_error <= args.tolerance
    )
    result = {
        "schema": "gamma.nncp_libnc_relative_parity.v1",
        "status": "PASS" if passed else "FAIL",
        "score_credit_bytes": 0,
        "exported_parameter_types": exported_types,
        "compute_dtype": args.compute_dtype,
        "device": str(device),
        "tolerance": args.tolerance,
        "rows": len(symbols),
        "maximum_absolute_probability_error": float(error.max()),
        "mean_absolute_probability_error": float(error.mean()),
        "maximum_distribution_sum_error": float(
            (student.sum(dim=-1) - 1).abs().max()
        ),
        "online_learning_rate": args.online_lr,
        "gradient_clip": args.gradient_clip if args.online_lr is not None else None,
        "segment_losses": losses,
        "maximum_absolute_parameter_error": max_parameter_error,
        "parameter_maximum_errors": final_parameter_error,
        "claims": {
            "frozen_minimal_distribution_parity": passed,
            "bf16_full_profile_parity": False,
            "online_update_parity": passed and args.online_lr is not None,
            "codec_roundtrip": False,
            "compression_improvement": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
