#!/usr/bin/env python3
"""Replay the bound update with LibNC's causal decoder graph schedule."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

import nncp_libnc_relative_parity as base
import nncp_v33_libnc_rmsnorm_backward_order_parity as rms_order
import nncp_v33_libnc_tanh_gelu_online_update_parity as gelu_replay


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_decoder_graph_update_parity_v1"


def libnc_rms_norm(
    value: torch.Tensor, gain: torch.Tensor, bias: torch.Tensor
) -> torch.Tensor:
    return rms_order.OutputOrderRMSNorm.apply(value) * gain + bias


def shifted_relative_row(raw: torch.Tensor, position: int, segment: int) -> torch.Tensor:
    rows = [torch.zeros_like(raw) for _ in range(segment)]
    rows[position] = raw
    staged = torch.stack(rows, dim=1)
    return base.relative_shift(staged)[:, position : position + 1, :]


def decoder_graph_segment(
    weights: dict[str, torch.Tensor],
    token: torch.Tensor,
    memory: torch.Tensor,
    segment: int,
    memory_length: int,
    heads: int,
    d_key: int,
    d_value: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Build one saved-node-style graph for each causal decoder position."""

    if token.ndim != 1 or token.shape[0] != segment:
        raise ValueError("decoder graph requires one stream and one segment")
    d_model = weights["embed"].shape[0]
    memory_key_value = F.linear(memory, weights["w_kv_0"])
    memory_key, memory_value = torch.split(
        memory_key_value, (heads * d_key, heads * d_value), dim=-1
    )
    memory_key = memory_key.view(memory_length, heads, d_key).permute(1, 0, 2)
    memory_value = memory_value.view(memory_length, heads, d_value).permute(
        1, 0, 2
    )
    current_keys: list[torch.Tensor] = []
    current_values: list[torch.Tensor] = []
    normalized_inputs: list[torch.Tensor] = []
    logits: list[torch.Tensor] = []
    relative_weight = weights["w_r_0"].permute(2, 1, 0)
    scale = math.sqrt(d_key * d_model)

    for position in range(segment):
        layer_input = (
            weights["embed"][:, token[position]].unsqueeze(0)
            * math.sqrt(d_model)
        )
        normalized = libnc_rms_norm(
            layer_input, weights["ln_g_0"], weights["ln_b_0"]
        )
        normalized_inputs.append(normalized)
        query = F.linear(normalized, weights["w_q_0"])
        key_value = F.linear(normalized, weights["w_kv_0"])
        key, value = torch.split(
            key_value, (heads * d_key, heads * d_value), dim=-1
        )
        query = query.view(1, heads, d_key).permute(1, 0, 2)
        key = key.view(1, heads, d_key).permute(1, 0, 2)
        value = value.view(1, heads, d_value).permute(1, 0, 2)
        current_keys.append(key)
        current_values.append(value)

        future = segment - position - 1
        key_parts = [memory_key, *current_keys]
        value_parts = [memory_value, *current_values]
        if future:
            key_parts.append(
                torch.zeros(
                    heads,
                    future,
                    d_key,
                    dtype=key.dtype,
                    device=key.device,
                )
            )
            value_parts.append(
                torch.zeros(
                    heads,
                    future,
                    d_value,
                    dtype=value.dtype,
                    device=value.device,
                )
            )
        all_key = torch.cat(key_parts, dim=1)
        all_value = torch.cat(value_parts, dim=1)
        content = torch.einsum("hkd,htd->htk", all_key, query)
        raw_relative = torch.einsum("hkd,htd->htk", relative_weight, query)
        raw_relative = raw_relative + weights["b_r_0"].T[:, None, :] * scale
        relative = shifted_relative_row(raw_relative[:, 0, :], position, segment)
        score = (content + relative) / math.sqrt(d_key)
        if future:
            score = score.clone()
            score[:, :, memory_length + position + 1 :] = -torch.inf
        attention = torch.softmax(score, dim=-1)
        attended = torch.einsum("htk,hkd->htd", attention, all_value)
        attended = attended.permute(1, 0, 2).reshape(1, heads * d_value)
        layer_input = layer_input + F.linear(attended, weights["w_o_0"])
        feedforward_input = libnc_rms_norm(
            layer_input, weights["ln_g_1"], weights["ln_b_1"]
        )
        gate, value_ff = F.linear(
            feedforward_input, weights["ff1_0"], weights["ff_bias1_0"]
        ).chunk(2, dim=-1)
        hidden = gelu_replay.libnc_gelu(gate) * value_ff
        layer_input = layer_input + F.linear(
            hidden, weights["ff2_0"], weights["ff_bias2_0"]
        )
        final = libnc_rms_norm(
            layer_input, weights["ln_g_2"], weights["ln_b_2"]
        )
        logits.append(F.linear(final, weights["embed_out"], weights["out_bias"]))

    next_memory = torch.cat((memory, torch.cat(normalized_inputs, dim=0)), dim=0)[
        -memory_length:
    ]
    return torch.cat(logits, dim=0), next_memory


def run_once(
    initial: dict[str, torch.Tensor],
    symbols: np.ndarray,
    learning_rate: float,
    gradient_clip: float,
) -> tuple[torch.Tensor, dict[str, torch.Tensor], list[float]]:
    base.forward_segment = decoder_graph_segment
    return base.evaluate_online(
        initial,
        symbols,
        4,
        4,
        2,
        8,
        8,
        torch.device("cpu"),
        torch.float32,
        learning_rate,
        gradient_clip,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--export",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/nncp_v33_relative_parity_v1/"
            "run_05/export"
        ),
    )
    parser.add_argument(
        "--trace",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/nncp_v33_online_update_parity_v1/"
            "run_07_bound/teacher.bin"
        ),
    )
    parser.add_argument(
        "--final-export",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/nncp_v33_online_update_parity_v1/"
            "run_07_bound/final_export"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / CANDIDATE_ID / "decision.json",
    )
    parser.add_argument("--learning-rate", type=float, default=0.00016)
    parser.add_argument("--gradient-clip", type=float, default=0.05)
    parser.add_argument("--tolerance", type=float, default=2e-5)
    args = parser.parse_args()

    initial, exported_types = base.load_export(args.export)
    symbols, distributions = base.load_trace(args.trace)
    teacher = torch.from_numpy(np.stack(distributions))
    teacher_final, _ = base.load_export(args.final_export)
    first_probabilities, first_final, losses = run_once(
        initial, symbols, args.learning_rate, args.gradient_clip
    )
    second_probabilities, second_final, second_losses = run_once(
        initial, symbols, args.learning_rate, args.gradient_clip
    )
    probability_error = (first_probabilities - teacher).abs()
    parameter_errors = {
        name: float((first_final[name] - teacher_final[name]).abs().max())
        for name in sorted(first_final)
    }
    maximum_parameter_error = max(parameter_errors.values())
    first_hash = gelu_replay.final_hash(first_final)
    second_hash = gelu_replay.final_hash(second_final)
    repeated = (
        first_hash == second_hash
        and torch.equal(first_probabilities, second_probabilities)
        and losses == second_losses
    )
    passed = (
        float(probability_error.max()) <= args.tolerance
        and maximum_parameter_error <= args.tolerance
        and repeated
    )
    result = {
        "schema": "gamma.nncp_v33_libnc_decoder_graph_update_parity.v1",
        "candidate_id": CANDIDATE_ID,
        "status": "PASS" if passed else "REJECT",
        "score_credit_bytes": 0,
        "contract": {
            "symbols": len(symbols),
            "decoder_states": 4,
            "updates": 1,
            "learning_rate": args.learning_rate,
            "gradient_clip": args.gradient_clip,
            "tolerance": args.tolerance,
            "graph_schedule": "causal_state_major_saved_key_value_nodes",
            "activation": "libnc_unfused_f32_tanh_formula",
            "rmsnorm_backward": (
                "inverse_times_gradient_minus_output_mean_gradient_output"
            ),
            "exported_parameter_types": exported_types,
        },
        "inputs": {
            "initial_manifest_sha256": gelu_replay.sha256(
                args.export / "manifest.json"
            ),
            "teacher_trace_sha256": gelu_replay.sha256(args.trace),
            "final_manifest_sha256": gelu_replay.sha256(
                args.final_export / "manifest.json"
            ),
            "script_sha256": gelu_replay.sha256(Path(__file__).resolve()),
        },
        "proof": {
            "maximum_absolute_probability_error": float(probability_error.max()),
            "mean_absolute_probability_error": float(probability_error.mean()),
            "maximum_absolute_parameter_error": maximum_parameter_error,
            "parameter_maximum_errors": parameter_errors,
            "segment_losses": losses,
            "first_final_tensor_sha256": first_hash,
            "second_final_tensor_sha256": second_hash,
            "repeat_byte_identical": repeated,
        },
        "decision": {
            "promotion_authorized": passed,
            "authorized_next_action": (
                "run the next faithful-profile constructive gate"
                if passed
                else "retire the decoder-graph schedule as sufficient"
            ),
            "forecast_bytes": 109389323,
            "verified_full_1g_score_bytes": None,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
