#!/usr/bin/env python3
"""Replay the bound NNCP miniature with the measured LibNC tanh GELU."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import torch

import nncp_libnc_relative_parity as base


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def libnc_gelu(value: torch.Tensor, approximate: str = "none") -> torch.Tensor:
    """LibNC nc_gelu F32 operation order measured by the primitive gate."""
    del approximate
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


def final_hash(parameters: dict[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for name in sorted(parameters):
        tensor = parameters[name].contiguous()
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def run_once(
    initial: dict[str, torch.Tensor], symbols, learning_rate: float,
    gradient_clip: float,
) -> tuple[torch.Tensor, dict[str, torch.Tensor], list[float]]:
    base.F.gelu = libnc_gelu
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
    parser = argparse.ArgumentParser()
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
        default=ROOT
        / "results/nncp_v33_libnc_tanh_gelu_online_update_parity_v1/decision.json",
    )
    parser.add_argument("--learning-rate", type=float, default=0.00016)
    parser.add_argument("--gradient-clip", type=float, default=0.05)
    parser.add_argument("--tolerance", type=float, default=2e-5)
    args = parser.parse_args()

    initial, exported_types = base.load_export(args.export)
    symbols, distributions = base.load_trace(args.trace)
    teacher = torch.from_numpy(__import__("numpy").stack(distributions))
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
    first_final_hash = final_hash(first_final)
    second_final_hash = final_hash(second_final)
    repeat_identical = (
        first_final_hash == second_final_hash
        and torch.equal(first_probabilities, second_probabilities)
        and losses == second_losses
    )
    passed = (
        float(probability_error.max()) <= args.tolerance
        and maximum_parameter_error <= args.tolerance
        and repeat_identical
    )
    decision = {
        "schema": "gamma.nncp_v33_libnc_tanh_gelu_online_update_parity.v1",
        "candidate_id": "nncp_v33_libnc_tanh_gelu_online_update_parity_v1",
        "status": "PASS" if passed else "REJECT",
        "score_credit_bytes": 0,
        "contract": {
            "layers": 1,
            "d_model": 32,
            "symbols": len(symbols),
            "updates": 1,
            "learning_rate": args.learning_rate,
            "gradient_clip": args.gradient_clip,
            "tolerance": args.tolerance,
            "activation": "libnc_unfused_f32_tanh_formula",
            "exported_parameter_types": exported_types,
        },
        "inputs": {
            "initial_manifest": {
                "path": str(args.export / "manifest.json"),
                "sha256": sha256(args.export / "manifest.json"),
            },
            "teacher_trace": {
                "path": str(args.trace),
                "sha256": sha256(args.trace),
            },
            "final_manifest": {
                "path": str(args.final_export / "manifest.json"),
                "sha256": sha256(args.final_export / "manifest.json"),
            },
            "primitive_decision": {
                "path": str(
                    ROOT
                    / "results/nncp_v33_libnc_activation_backward_parity_v1/"
                    "decision.json"
                ),
                "sha256": sha256(
                    ROOT
                    / "results/nncp_v33_libnc_activation_backward_parity_v1/"
                    "decision.json"
                ),
            },
        },
        "proof": {
            "maximum_absolute_probability_error": float(
                probability_error.max()
            ),
            "mean_absolute_probability_error": float(probability_error.mean()),
            "maximum_absolute_parameter_error": maximum_parameter_error,
            "parameter_maximum_errors": parameter_errors,
            "segment_losses": losses,
            "first_final_tensor_sha256": first_final_hash,
            "second_final_tensor_sha256": second_final_hash,
            "repeat_byte_identical": repeat_identical,
        },
        "decision": {
            "promotion_authorized": passed,
            "authorized_next_action": (
                "localize the next mismatched primitive or run frozen full-profile parity"
                if passed
                else "retire tanh GELU as a sufficient online-update parity fix"
            ),
            "verified_full_1g_score_bytes": None,
            "forecast_bytes": 109389323,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
